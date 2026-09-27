Incident: The order-processing-service is live in production, but the on-call team just flagged that its AWS X-Ray traces are incomplete. Segments show up in the console, but DynamoDB calls never appear, and some traces fail to close properly. You've been asked to fix the instrumentation in order_service.py before the next deploy.

To let you run and fix this without real AWS credentials, the project includes two lightweight local stand-ins that mirror the real SDKs you used in the course:

    xray_mock.py — mimics aws_xray_sdk.core: xray_recorder.configure(), patch_all(), begin_segment() / end_segment(), and begin_subsegment() / end_subsegment().
    boto3_mock.py — mimics boto3's DynamoDB resource. Its Table only gets automatically instrumented if patch_all() already ran before the resource/table was created — exactly like the real X-Ray boto3 patcher.

Do not edit xray_mock.py, boto3_mock.py, or main.py. Only edit order_service.py.

There are three separate instrumentation bugs to find and fix in order_service.py:

    Recorder setup order — configuration, patching, and client creation are not happening in the right sequence, so the service is effectively running unconfigured or half-patched.
    Missing automatic instrumentation — the DynamoDB client/table is created at the wrong time relative to patch_all(), so its calls never generate subsegments.
    An improperly scoped custom subsegment — the ValidateOrder subsegment isn't guaranteed to close on every code path, which leaves the trace segment unable to close cleanly.

Run the practice (via the Run button) to execute main.py, which processes a sample order and inspects the resulting trace. It prints PASSED with a clean trace summary once every issue is fixed, or FAILED with a specific list of what's still wrong.

Goal: every run of process_order(...) should produce a complete trace: recorder configured → SDK patched → DynamoDB client created → segment opened → ValidateOrder subsegment opened and closed → automatic DynamoDB::PutItem subsegment recorded → segment closed cleanly with nothing left dangling.

```python
# boto3_mock.py

"""
Lightweight local mock of boto3's DynamoDB resource, wired to xray_mock so
that automatic instrumentation only produces subsegments when patch_all()
already ran *before* the resource/table was created - exactly like the
real aws-xray-sdk boto3 patcher.
"""
import xray_mock as _xm


class _Table:
    def __init__(self, name, patched_at_creation):
        self.name = name
        self._patched_at_creation = patched_at_creation

    def _call(self, operation, **kwargs):
        if self._patched_at_creation:
            _xm.xray_recorder.begin_subsegment(f"DynamoDB::{operation}")
            try:
                result = {"status": "ok", "operation": operation, "kwargs": kwargs}
            finally:
                _xm.xray_recorder.end_subsegment()
            return result
        return {"status": "ok", "operation": operation, "kwargs": kwargs}

    def put_item(self, **kwargs):
        return self._call("PutItem", **kwargs)

    def get_item(self, **kwargs):
        return self._call("GetItem", **kwargs)


class _DynamoDBResource:
    def __init__(self):
        # Whether patch_all() already ran at the moment this resource
        # (and therefore any Table it creates) came into existence.
        self._patched_at_creation = _xm.is_boto3_patched()

    def Table(self, name):
        return _Table(name, self._patched_at_creation)


def resource(service_name):
    if service_name == "dynamodb":
        return _DynamoDBResource()
    raise ValueError(f"Mock boto3 does not support resource type: {service_name}")


# main.py

import sys

import order_service
import xray_mock


def check(cond, msg, failures):
    if not cond:
        failures.append(msg)


def main():
    failures = []

    try:
        order_service.process_order(
            {
                "order_id": "ORD-1001",
                "customer": "Acme Corp",
                "items": [{"sku": "WIDGET-1", "qty": 3}],
                "total": 149.97,
            }
        )
    except Exception as e:
        print(f"FAILED - process_order raised an exception: {e}")
        sys.exit(1)

    trace_log = xray_mock.xray_recorder.trace_log
    events = [e[0] for e in trace_log]

    check("configure" in events, "xray_recorder.configure() was never called.", failures)
    check("patch_all" in events, "patch_all() was never called - automatic AWS SDK tracing is missing.", failures)
    check("begin_segment" in events, "xray_recorder.begin_segment() was never called.", failures)
    check("end_segment" in events, "xray_recorder.end_segment() was never called - the segment was left open.", failures)

    if "configure" in events and "patch_all" in events:
        check(
            events.index("configure") < events.index("patch_all"),
            "configure() must run before patch_all() as part of service startup, not after tracing has already begun.",
            failures,
        )
    if "patch_all" in events and "begin_segment" in events:
        check(
            events.index("patch_all") < events.index("begin_segment"),
            "patch_all() must run before the segment begins (and before any client it should instrument is created).",
            failures,
        )

    begins = [e[1] for e in trace_log if e[0] == "begin_subsegment"]
    ends = [e[1] for e in trace_log if e[0] == "end_subsegment"]
    leaked = [e[1] for e in trace_log if e[0] == "leaked_subsegment"]

    check(
        any("Validate" in name for name in begins),
        "No custom subsegment around order validation (e.g. 'ValidateOrder') was found.",
        failures,
    )
    check(
        not leaked,
        f"Subsegment(s) never closed and had to be force-closed when the segment ended: {leaked}. "
        "Make sure every begin_subsegment() has a matching end_subsegment() on every code path.",
        failures,
    )
    check(
        len(begins) == len(ends),
        f"Mismatched subsegments: {len(begins)} opened vs {len(ends)} explicitly closed.",
        failures,
    )
    check(
        any(name.startswith("DynamoDB::") for name in begins),
        "No automatic 'DynamoDB::*' subsegment was recorded - the DynamoDB client was likely created before patch_all() ran.",
        failures,
    )
    check(
        xray_mock.xray_recorder._segment is not None and xray_mock.xray_recorder._segment.closed,
        "The X-Ray segment was never properly closed.",
        failures,
    )

    if failures:
        print("FAILED - the trace is still incomplete:")
        for f in failures:
            print(f" - {f}")
        sys.exit(1)
    else:
        print(
            "PASSED - X-Ray trace is complete: configure -> patch_all -> segment -> "
            "ValidateOrder subsegment -> DynamoDB::PutItem subsegment -> segment closed cleanly."
        )
        print("Trace log:", trace_log)
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/bin/bash
python3 main.py

# order_service.py
"""
Order Processing Service
-------------------------
Production incident: this service's X-Ray traces are showing up in the
console incomplete - DynamoDB calls never appear, and some traces don't
close cleanly.

xray_mock and boto3_mock are lightweight local stand-ins for the real
aws_xray_sdk.core and boto3 APIs you used in the course, so this can run
and be graded without real AWS credentials. The method names and
semantics (configure, patch_all, begin_segment/end_segment,
begin_subsegment/end_subsegment) mirror the real SDK.
"""

import boto3_mock as boto3
from xray_mock import xray_recorder, patch_all

# BUG: the DynamoDB resource/table is created here, before patch_all()
# has run, so this client never gets automatically instrumented.
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Orders")

patch_all()


def configure_tracing():
    """Set up the X-Ray recorder for this service."""
    xray_recorder.configure(service="order-processing-service")


def validate_order(order):
    # BUG: the subsegment is only closed on the error path. If validation
    # succeeds, it's never closed, leaving it dangling when the segment
    # tries to end.
    subsegment = xray_recorder.begin_subsegment("ValidateOrder")
    if not order.get("items"):
        xray_recorder.end_subsegment()
        raise ValueError("Order has no items")
    subsegment.put_annotation("order_id", order["order_id"])
    return True


def save_order_to_dynamodb(order):
    return table.put_item(Item=order)


def process_order(order):
    xray_recorder.begin_segment("order-processing-service")

    # BUG: the recorder is configured here, after the segment has already
    # begun, instead of once at service startup before any tracing calls.
    configure_tracing()

    validate_order(order)
    result = save_order_to_dynamodb(order)

    xray_recorder.end_segment()
    return result

# xray_mock.py
"""
Lightweight local mock of the aws_xray_sdk.core API. Mimics enough of the
real AWS X-Ray SDK for Python (recorder configuration, segments, and
subsegments) so this exercise can run offline while exercising the same
patterns used with the real SDK.
"""


class Subsegment:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.children = []
        self.closed = False
        self.leaked = False
        self.annotations = {}

    def put_annotation(self, key, value):
        self.annotations[key] = value


class Segment:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.closed = False


class XRayRecorder:
    def __init__(self):
        self._configured = False
        self._service_name = None
        self._segment = None
        self._subsegment_stack = []
        self.trace_log = []  # flat, ordered log of every tracing call made

    def configure(self, service=None, sampling=None, **kwargs):
        self._configured = True
        self._service_name = service
        self.trace_log.append(("configure", service))

    def begin_segment(self, name):
        self._segment = Segment(name)
        self._subsegment_stack = []
        self.trace_log.append(("begin_segment", name))
        return self._segment

    def end_segment(self):
        if self._segment is None:
            raise RuntimeError("No active segment to end")
        # Mirrors real-world behavior: subsegments left open when the
        # segment ends get force-closed and flagged as leaked/incomplete.
        while self._subsegment_stack:
            leaked = self._subsegment_stack.pop()
            leaked.closed = True
            leaked.leaked = True
            self.trace_log.append(("leaked_subsegment", leaked.name))
        self._segment.closed = True
        self.trace_log.append(("end_segment", self._segment.name))

    def begin_subsegment(self, name):
        if self._segment is None:
            raise RuntimeError("Cannot begin a subsegment without an active segment")
        parent = self._subsegment_stack[-1] if self._subsegment_stack else self._segment
        sub = Subsegment(name, parent)
        parent.children.append(sub)
        self._subsegment_stack.append(sub)
        self.trace_log.append(("begin_subsegment", name))
        return sub

    def end_subsegment(self):
        if not self._subsegment_stack:
            raise RuntimeError("No open subsegment to end")
        sub = self._subsegment_stack.pop()
        sub.closed = True
        self.trace_log.append(("end_subsegment", sub.name))

    def current_segment(self):
        return self._segment


xray_recorder = XRayRecorder()

_PATCHED = {"boto3": False}


def patch_all():
    _PATCHED["boto3"] = True
    xray_recorder.trace_log.append(("patch_all", None))


def is_boto3_patched():
    return _PATCHED["boto3"]


```
