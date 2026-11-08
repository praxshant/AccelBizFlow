import json
import os
import re
import uuid
from datetime import datetime, timezone

from app.database import ConversationMessageRecord, ConversationRecord
from app.schemas.advisor import AdvisorMessageResponse, ConversationResponse
from app.schemas.eligibility import BusinessProfile, RecommendationRequest
from app.services.advisor.providers import (
    AdvisorMessage,
    AdvisorProviderError,
    OllamaProvider,
)


FIELDS = ("business_type", "segment", "city_tier", "employees", "sites", "gstin_active")


class ConversationService:
    def __init__(self, app):
        self.app = app
        self.session_factory = app.state.db_session

    def _extract_deterministic(self, text: str, current: dict) -> dict:
        value = dict(current)
        lower = text.lower()

        # Business type detection (English + Hinglish)
        if any(w in lower for w in ("clinic", "hospital", "dawakhana")):
            value["business_type"] = "clinic"
        elif any(w in lower for w in ("office", "daftar", "agency", "consulting")):
            value["business_type"] = "office"
        elif any(w in lower for w in ("retail", "shop", "kirana", "dukan", "store")):
            value["business_type"] = "retail"
        elif any(w in lower for w in ("bakery", "baking", "cafe", "restaurant")):
            value["business_type"] = "retail"
        elif any(w in lower for w in ("factory", "karkhana", "plant", "manufacturing")):
            value["business_type"] = "manufacturing"

        # Segment detection (English + Hinglish)
        if any(w in lower for w in ("multi-site", "multisite", "multiple sites", "kai jagah")):
            value["segment"] = "multi"
        elif any(w in lower for w in ("professional", "consultant", "advisor", "advocate")):
            value["segment"] = "prof"
        elif any(w in lower for w in ("manufacturer", "factory", "karkhana")):
            value["segment"] = "mfg"
        elif any(w in lower for w in ("micro", "chhota")):
            value["segment"] = "micro"
        elif any(w in lower for w in ("bakery", "baking", "cafe", "restaurant", "small business")):
            value["segment"] = "micro"

        # Employee count (English + Hinglish: log, karmchari, staff, employees)
        employee = re.search(r"(\d+)\s*(?:employees?|staff|log|karmchari|workers?|people|bande)", lower)
        if employee:
            value["employees"] = int(employee.group(1))

        # Site count (English + Hinglish: jagah, dukan, branch, sites)
        site = re.search(r"(\d+)\s*(?:sites?|locations?|branches?|outlets?|dukan|jagah)", lower)
        if site:
            value["sites"] = int(site.group(1))

        # City tier detection
        tier1_cities = {
            "mumbai", "delhi", "bangalore", "bengaluru", "chennai",
            "kolkata", "hyderabad", "pune", "ahmedabad", "surat",
        }
        tier2_cities = {"jaipur", "lucknow", "kanpur", "nagpur", "indore", "bhopal", "patna", "coimbatore"}
        if "tier 1" in lower or any(city in lower for city in tier1_cities):
            value["city_tier"] = 1
        elif "tier 2" in lower or "tier2" in lower or any(city in lower for city in tier2_cities):
            value["city_tier"] = 2

        # GSTIN detection (English + Hinglish)
        if re.search(r"gst hai|gstin hai|have gst|active gst|gst yes|yes.*gst|gst.*yes|haan.*gst|gst.*haan|gst hai", lower):
            value["gstin_active"] = True
        elif re.search(r"gst nahi|no gst|gst.*no|no.*gst|without gst|gst nhi", lower):
            value["gstin_active"] = False
        elif "gstin" in lower and ("yes" in lower or "active" in lower or "registered" in lower):
            value["gstin_active"] = True
        elif "gstin" in lower and ("no" in lower or "inactive" in lower or "not" in lower):
            value["gstin_active"] = False

        return value

    def _extract_answer_to_question(self, text: str, current: dict, history) -> dict:
        if not history:
            return {}
        last_question = next(
            (item.content.lower() for item in reversed(history) if item.role == "assistant"),
            "",
        )
        lower = text.lower().strip()
        answer = {}
        if "what type of business" in last_question:
            if any(word in lower for word in ("bakery", "baking", "cafe", "restaurant", "shop", "retail")):
                answer["business_type"] = "retail"
        elif "professional, multi-site, micro retail, or manufacturing" in last_question:
            if any(word in lower for word in ("micro", "small", "retail", "bakery")):
                answer["segment"] = "micro"
            elif "professional" in lower:
                answer["segment"] = "prof"
            elif "multi" in lower:
                answer["segment"] = "multi"
            elif "manufactur" in lower:
                answer["segment"] = "mfg"
        elif "tier 1 or tier 2" in last_question:
            if "2" in lower or "tier two" in lower:
                answer["city_tier"] = 2
            elif "1" in lower or "tier one" in lower:
                answer["city_tier"] = 1
        elif "how many employees" in last_question:
            match = re.search(r"\b\d+\b", lower)
            if match:
                answer["employees"] = int(match.group())
        elif "how many sites" in last_question:
            match = re.search(r"\b\d+\b", lower)
            if match:
                answer["sites"] = int(match.group())
        elif "active gstin" in last_question:
            if lower in {"yes", "y", "haan", "ha", "ji", "yes hai"}:
                answer["gstin_active"] = True
            elif lower in {"no", "n", "nahi", "nahin", "nhi"}:
                answer["gstin_active"] = False
        return {key: value for key, value in answer.items() if key not in current}

    def _provider_extract(self, messages, current):
        if os.getenv("ADVISOR_PROVIDER", "").lower() != "ollama":
            return {}
        try:
            result = OllamaProvider().extract_profile(messages)
            return {key: result[key] for key in FIELDS if result.get(key) is not None}
        except AdvisorProviderError:
            return {}

    def _load(self, session, conversation_id):
        record = session.get(ConversationRecord, conversation_id)
        if record is None:
            record = ConversationRecord(conversation_id=conversation_id, profile_json="{}")
            session.add(record)
            session.flush()
        messages = session.query(ConversationMessageRecord).filter_by(
            conversation_id=conversation_id
        ).order_by(ConversationMessageRecord.message_id).all()
        return record, messages

    def message(self, conversation_id: str | None, text: str) -> AdvisorMessageResponse:
        cid = conversation_id or str(uuid.uuid4())
        with self.session_factory.begin() as session:
            record, history = self._load(session, cid)
            profile = json.loads(record.profile_json)
            profile.update(self._extract_deterministic(text, profile))
            profile.update(self._extract_answer_to_question(text, profile, history))
            provider_values = self._provider_extract(
                [AdvisorMessage(item.role, item.content) for item in history]
                + [AdvisorMessage("user", text)],
                profile,
            )
            for key, value in provider_values.items():
                if key not in profile:
                    profile[key] = value
            session.add(ConversationMessageRecord(conversation_id=cid, role="user", content=text))
            record.profile_json = json.dumps(profile)
            record.updated_at = datetime.now(timezone.utc)
            missing = [field for field in FIELDS if field not in profile]
            if missing:
                questions = {
                    "business_type": "What type of business do you operate?",
                    "segment": "Would you describe it as professional, multi-site, micro retail, or manufacturing?",
                    "city_tier": "Is your city Tier 1 or Tier 2?",
                    "employees": "How many employees or staff do you have?",
                    "sites": "How many sites or locations need service?",
                    "gstin_active": "Do you have an active GSTIN? Please answer yes or no.",
                }
                reply = questions[missing[0]]
                session.add(ConversationMessageRecord(conversation_id=cid, role="assistant", content=reply))
                return AdvisorMessageResponse(
                    conversation_id=cid,
                    reply=reply,
                    profile=profile,
                    missing_fields=missing,
                )
            try:
                validated = BusinessProfile.model_validate(profile)
            except ValueError:
                reply = "I could not validate that business information. Please correct the requested values."
                return AdvisorMessageResponse(conversation_id=cid, reply=reply, missing_fields=[])
            recommendation = self.app.state.eligibility.recommend(
                RecommendationRequest(profile=validated)
            )
            bundle_names = [b.name for b in recommendation.bundles if b.product_ids]
            eligible_names = [d.product.product_name for d in recommendation.eligible_products[:3]]
            reply = (
                f"Great! Based on your profile, I found {len(recommendation.eligible_products)} eligible products. "
                f"Top picks include: {', '.join(eligible_names)}{'...' if len(recommendation.eligible_products) > 3 else ''}. "
                f"I've prepared {len(bundle_names)} bundle option(s): {', '.join(bundle_names)}. "
                "Share the bundle you prefer and I'll generate a quote instantly."
            )
            session.add(ConversationMessageRecord(conversation_id=cid, role="assistant", content=reply))
            return AdvisorMessageResponse(
                conversation_id=cid, reply=reply, profile=validated,
                recommendations=recommendation
            )

    def get(self, cid: str) -> ConversationResponse:
        with self.session_factory() as session:
            record = session.get(ConversationRecord, cid)
            if record is None:
                raise KeyError(cid)
            messages = session.query(ConversationMessageRecord).filter_by(
                conversation_id=cid
            ).order_by(ConversationMessageRecord.message_id).all()
            profile = json.loads(record.profile_json)
            return ConversationResponse(
                conversation_id=cid,
                messages=[{"role": item.role, "content": item.content} for item in messages],
                profile=BusinessProfile.model_validate(profile) if len(profile) == len(FIELDS) else None,
            )
