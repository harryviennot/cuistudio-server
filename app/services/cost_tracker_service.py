"""
Cost Tracker Service
Tracks AI API costs per extraction for benchmarking and monitoring.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from supabase import Client

logger = logging.getLogger(__name__)


class CostTrackerService:
    """
    Service for tracking AI API costs per extraction.

    Features:
    - Records costs for each AI API call
    - Aggregates costs by job, day, provider, and type
    - Enables benchmarking of old vs new methods
    """

    # Pricing per 1M tokens (as of Dec 2024)
    PRICING = {
        "gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
        "gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
        "gemini-3-flash-preview-audio": {"input": 1.00, "output": 3.00},  # Audio input pricing
        "gemini-2.5-flash-image": {"per_image": 0.039},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    # Fixed costs
    FIXED_COSTS = {
        "flux": 0.04,  # Per image
        "whisper_local": 0.0,  # Free (local processing)
    }

    def __init__(self, supabase: Client):
        """
        Initialize CostTrackerService.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase

    async def record_cost(
        self,
        extraction_job_id: str,
        service_provider: str,
        service_type: str,
        model_name: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        audio_seconds: Optional[float] = None,
        images_processed: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
        estimated_cost_usd: Optional[float] = None
    ) -> Optional[str]:
        """
        Record a cost entry for an AI API call.

        Args:
            extraction_job_id: UUID of the extraction job
            service_provider: Provider name (gemini, openai, flux, whisper_local)
            service_type: Type of call (transcription, text_extraction, vision, image_generation)
            model_name: Specific model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            audio_seconds: Duration of audio processed
            images_processed: Number of images processed
            processing_time_ms: Processing time in milliseconds
            estimated_cost_usd: Pre-calculated cost, or None to auto-calculate

        Returns:
            UUID of the created cost record, or None if failed
        """
        try:
            # Auto-calculate cost if not provided
            if estimated_cost_usd is None:
                estimated_cost_usd = self._calculate_cost(
                    service_provider=service_provider,
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    audio_seconds=audio_seconds,
                    images_processed=images_processed
                )

            cost_data = {
                "extraction_job_id": extraction_job_id,
                "service_provider": service_provider,
                "service_type": service_type,
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "audio_seconds": audio_seconds,
                "images_processed": images_processed,
                "estimated_cost_usd": float(estimated_cost_usd) if estimated_cost_usd else None,
                "processing_time_ms": processing_time_ms
            }

            result = await asyncio.to_thread(
                lambda: self.supabase.table("extraction_costs")
                    .insert(cost_data)
                    .execute()
            )

            if result.data and len(result.data) > 0:
                cost_id = result.data[0].get("id")
                logger.debug(
                    f"Recorded cost: {service_provider}/{service_type} "
                    f"${estimated_cost_usd:.6f} for job {extraction_job_id}"
                )
                return cost_id

            return None

        except Exception as e:
            logger.error(f"Failed to record cost: {e}")
            return None

    async def get_job_costs(self, extraction_job_id: str) -> List[Dict[str, Any]]:
        """
        Get all cost entries for a specific extraction job.

        Args:
            extraction_job_id: UUID of the extraction job

        Returns:
            List of cost records
        """
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("extraction_costs")
                    .select("*")
                    .eq("extraction_job_id", extraction_job_id)
                    .order("created_at")
                    .execute()
            )
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get job costs: {e}")
            return []

    async def get_job_total_cost(self, extraction_job_id: str) -> float:
        """
        Get total cost for a specific extraction job.

        Args:
            extraction_job_id: UUID of the extraction job

        Returns:
            Total cost in USD
        """
        costs = await self.get_job_costs(extraction_job_id)
        return sum(c.get("estimated_cost_usd", 0) or 0 for c in costs)

    async def get_daily_summary(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get cost summary for a specific day.

        Args:
            date: Date to get summary for (defaults to today)

        Returns:
            Summary dict with totals by provider and type
        """
        if date is None:
            date = datetime.now(timezone.utc)

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("extraction_costs")
                    .select("*")
                    .gte("created_at", start_of_day.isoformat())
                    .lt("created_at", end_of_day.isoformat())
                    .execute()
            )

            costs = result.data or []

            # Aggregate by provider
            by_provider: Dict[str, float] = {}
            by_type: Dict[str, float] = {}
            total_cost = 0.0
            total_extractions = set()

            for cost in costs:
                amount = cost.get("estimated_cost_usd", 0) or 0
                provider = cost.get("service_provider", "unknown")
                service_type = cost.get("service_type", "unknown")
                job_id = cost.get("extraction_job_id")

                total_cost += amount
                by_provider[provider] = by_provider.get(provider, 0) + amount
                by_type[service_type] = by_type.get(service_type, 0) + amount

                if job_id:
                    total_extractions.add(job_id)

            return {
                "date": start_of_day.date().isoformat(),
                "total_cost_usd": round(total_cost, 6),
                "total_extractions": len(total_extractions),
                "total_api_calls": len(costs),
                "by_provider": {k: round(v, 6) for k, v in by_provider.items()},
                "by_type": {k: round(v, 6) for k, v in by_type.items()},
            }

        except Exception as e:
            logger.error(f"Failed to get daily summary: {e}")
            return {
                "date": start_of_day.date().isoformat(),
                "total_cost_usd": 0,
                "total_extractions": 0,
                "total_api_calls": 0,
                "by_provider": {},
                "by_type": {},
                "error": str(e)
            }

    async def get_method_comparison(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Compare costs between old and new methods over a period.

        Args:
            days: Number of days to analyze

        Returns:
            Comparison dict with cost/count breakdown by method
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("extraction_costs")
                    .select("*")
                    .gte("created_at", start_date.isoformat())
                    .lt("created_at", end_date.isoformat())
                    .execute()
            )

            costs = result.data or []

            # Group by model/method
            methods: Dict[str, Dict[str, Any]] = {}

            for cost in costs:
                model = cost.get("model_name") or cost.get("service_provider", "unknown")
                amount = cost.get("estimated_cost_usd", 0) or 0
                processing_time = cost.get("processing_time_ms", 0) or 0

                if model not in methods:
                    methods[model] = {
                        "total_cost": 0.0,
                        "call_count": 0,
                        "total_processing_ms": 0
                    }

                methods[model]["total_cost"] += amount
                methods[model]["call_count"] += 1
                methods[model]["total_processing_ms"] += processing_time

            # Calculate averages
            for model, stats in methods.items():
                if stats["call_count"] > 0:
                    stats["avg_cost_per_call"] = round(
                        stats["total_cost"] / stats["call_count"], 6
                    )
                    stats["avg_processing_ms"] = round(
                        stats["total_processing_ms"] / stats["call_count"], 2
                    )
                stats["total_cost"] = round(stats["total_cost"], 6)

            return {
                "period_start": start_date.date().isoformat(),
                "period_end": end_date.date().isoformat(),
                "methods": methods
            }

        except Exception as e:
            logger.error(f"Failed to get method comparison: {e}")
            return {
                "period_start": start_date.date().isoformat(),
                "period_end": end_date.date().isoformat(),
                "methods": {},
                "error": str(e)
            }

    def _calculate_cost(
        self,
        service_provider: str,
        model_name: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        audio_seconds: Optional[float] = None,
        images_processed: Optional[int] = None
    ) -> float:
        """
        Calculate estimated cost based on usage.

        Args:
            service_provider: Provider name
            model_name: Specific model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            audio_seconds: Duration of audio (for transcription)
            images_processed: Number of images (for image generation)

        Returns:
            Estimated cost in USD
        """
        # Check fixed costs first
        if service_provider in self.FIXED_COSTS:
            if images_processed:
                return self.FIXED_COSTS[service_provider] * images_processed
            return self.FIXED_COSTS[service_provider]

        # Get model pricing
        model_key = model_name or service_provider
        pricing = self.PRICING.get(model_key)

        if not pricing:
            logger.warning(f"No pricing found for model: {model_key}")
            return 0.0

        cost = 0.0

        # Token-based pricing
        if "input" in pricing and input_tokens:
            cost += (input_tokens / 1_000_000) * pricing["input"]

        if "output" in pricing and output_tokens:
            cost += (output_tokens / 1_000_000) * pricing["output"]

        # Per-image pricing
        if "per_image" in pricing and images_processed:
            cost += pricing["per_image"] * images_processed

        # Audio pricing (tokens calculated from seconds)
        # Gemini: ~25 tokens per second of audio
        if audio_seconds and "input" in pricing:
            audio_tokens = int(audio_seconds * 25)
            cost += (audio_tokens / 1_000_000) * pricing["input"]

        return cost

    def estimate_cost(
        self,
        model_name: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        images: Optional[int] = None
    ) -> float:
        """
        Estimate cost for a planned API call (without recording).

        Args:
            model_name: Model to use
            input_tokens: Expected input tokens
            output_tokens: Expected output tokens
            images: Number of images to process/generate

        Returns:
            Estimated cost in USD
        """
        return self._calculate_cost(
            service_provider=model_name.split("-")[0] if model_name else "unknown",
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            images_processed=images
        )
