"""Lesson 4 reference policies for the demo's order investigation workflow."""

import json
from datetime import date

from .tools import execute, policy_for_model


class OptimizedInvestigation:
    def __init__(self, order_id, models):
        self.order_id = order_id
        self.models = models
        self.tracking_number = None
        self.conflict = True
        self.kind = None
        self.estimated_date = None
        self.completed = set()
        self.tool_failed = False
        self.retried_with_strong_model = False

    def prefetch(self):
        order = execute("get_order", {"order_id": self.order_id})
        self.kind = order["kind"]
        self.tracking_number = order["tracking_number"] if order["status"] == "in_transit" else None
        tracking = (
            execute("get_tracking", {"tracking_number": self.tracking_number})
            if self.tracking_number
            else None
        )
        self.conflict = order["evidence_conflict"] or bool(tracking and tracking["evidence_conflict"])
        if tracking:
            self.record_tracking(tracking)
        return {"order": order, "tracking": tracking}

    def record_tracking(self, tracking):
        self.conflict |= bool(tracking.get("evidence_conflict"))
        self.estimated_date = next(
            (event["estimated_delivery"] for event in reversed(tracking["events"]) if event.get("estimated_delivery")),
            None,
        )

    def phase(self):
        if self.tool_failed:
            return "工具查询失败。说明缺少哪些证据，并升级人工。"

        if not {"get_warehouse_events", "search_policy"} <= self.completed:
            return "先在同一次响应里发出仓库查询和政策检索。"
        required = {"get_policy_document"}
        if self.tracking_number:
            required.add("get_tracking")
        if not required <= self.completed:
            return "读取检索到的政策正文。已有运单号时，在同一次响应中复查物流。"
        return "按结论与证据、预计时间、下一步、政策依据答复，每项最多一句。"

    @property
    def ready_to_answer(self):
        needed = {"get_warehouse_events", "search_policy", "get_policy_document"}
        if self.tracking_number:
            needed.add("get_tracking")
        return needed <= self.completed and not self.tool_failed

    def update_request(self, request):
        request["messages"].append({"role": "user", "content": self.phase()})
        # Request messages are copied by the loop, so this phase instruction only lives here.
        if self.ready_to_answer or self.tool_failed:
            request["tools"] = []
            if self.models.get("simple") and self.ready_to_answer and not self.conflict and not self.retried_with_strong_model and self.kind == "delayed" and self.estimated_date:
                request["model"] = self.models["simple"]
        return request

    def record_tool(self, name, result, status):
        if status == "ok":
            self.completed.add(name)
            if name == "get_tracking":
                self.record_tracking(result)
        else:
            self.tool_failed = True

    def for_model(self, name, result):
        if name == "get_policy_document" and isinstance(result, str):
            return policy_for_model(result)
        return result

    def should_retry(self, request, message, finish_reason):
        if request["model"] != self.models.get("simple") or self.retried_with_strong_model:
            return False
        content = message.get("content") or ""
        estimated = date.fromisoformat(self.estimated_date)
        date_formats = (estimated.isoformat(), f"{estimated.month}月{estimated.day}日")
        compact = content.replace(" ", "")
        if (
            finish_reason == "stop"
            and all(field in content for field in ("结论", "预计时间", "下一步", "政策依据"))
            and any(value in compact for value in date_formats)
            and any(value in compact for value in ("非保证", "不保证", "仅供参考"))
            and "联系承运商" in compact
            and "中转站延误" in compact
            and "超过三天" in compact
        ):
            return False
        self.retried_with_strong_model = True
        return True

    def prefetch_message(self, evidence, user_text):
        return (
            user_text
            + "\n业务时点：" + evidence["order"]["as_of"]
            + "\n应用预取的订单和物流证据：" + json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))
        )
