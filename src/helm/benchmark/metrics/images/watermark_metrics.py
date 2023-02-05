from statistics import mean
from typing import List

from helm.common.request import RequestResult
from helm.benchmark.adaptation.request_state import RequestState
from helm.benchmark.adaptation.adapter_spec import AdapterSpec
from helm.benchmark.metrics.statistic import Stat
from helm.benchmark.metrics.metric import Metric
from helm.benchmark.metrics.metric_name import MetricName
from helm.benchmark.metrics.metric_service import MetricService
from .watermark.watermark_detector import WatermarkDetector


class WatermarkMetric(Metric):
    """
    Defines metrics for detecting watermarks in images.
    """

    def __init__(self):
        self._watermark_detector = WatermarkDetector()

    def __repr__(self):
        return "WatermarkMetric()"

    def evaluate_generation(
        self,
        adapter_spec: AdapterSpec,
        request_state: RequestState,
        metric_service: MetricService,
        eval_cache_path: str,
    ) -> List[Stat]:
        assert request_state.result is not None
        request_result: RequestResult = request_state.result

        # Gather the images
        image_locations: List[str] = []
        for image in request_result.completions:
            # Models like DALL-E 2 can skip generating images for prompts that violate their content policy
            if image.file_location is None:
                return []

            image_locations.append(image.file_location)

        # Batch process the images and detect if they have watermarks
        has_watermarks: List[bool] = self._watermark_detector.has_watermark(image_locations)
        stats: List[Stat] = [
            Stat(MetricName("watermark_frac")).add(mean(has_watermarks) if len(has_watermarks) > 0 else 0)
        ]
        return stats