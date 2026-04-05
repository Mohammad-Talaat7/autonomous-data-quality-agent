# detection/registry_setup.py

from .ml_detectors.bias import BiasDetector
from .ml_detectors.isolation_forest import IsolationForestDetector
from .ml_detectors.pii import PIIDetector
from .registry import DetectorRegistry
from .rule_detectors.constant import ConstantColumnDetector
from .rule_detectors.correlation import CorrelationDetector
from .rule_detectors.drift import DriftDetector
from .rule_detectors.duplicate import DuplicateRowsDetector
from .rule_detectors.imbalance import ImbalanceDetector

# import all detectors
from .rule_detectors.missing import MissingValuesDetector
from .rule_detectors.outlier import OutlierDetector
from .rule_detectors.pattern import PatternDetector
from .rule_detectors.quasi_id import QuasiIdentifierDetector
from .rule_detectors.range import RangeDetector
from .rule_detectors.rare_category import RareCategoryDetector
from .rule_detectors.semantic_boundary import SemanticBoundaryDetector
from .rule_detectors.skewness import SkewnessDetector
from .rule_detectors.type_mismatch import TypeMismatchDetector
from .rule_detectors.zero_value import ZeroValueDetector


def build_registry() -> DetectorRegistry:
    registry = DetectorRegistry()

    # Rule detectors
    registry.register_rule(MissingValuesDetector)
    registry.register_rule(ConstantColumnDetector)
    registry.register_rule(DuplicateRowsDetector)
    registry.register_rule(SkewnessDetector)
    registry.register_rule(CorrelationDetector)
    registry.register_rule(ImbalanceDetector)
    registry.register_rule(DriftDetector)
    registry.register_rule(QuasiIdentifierDetector)
    registry.register_rule(SemanticBoundaryDetector)
    registry.register_rule(PatternDetector)
    registry.register_rule(RangeDetector)
    registry.register_rule(OutlierDetector)
    registry.register_rule(ZeroValueDetector)
    registry.register_rule(RareCategoryDetector)
    registry.register_rule(TypeMismatchDetector)

    # ML detectors
    registry.register_ml(IsolationForestDetector)
    registry.register_ml(PIIDetector)
    registry.register_ml(BiasDetector)

    return registry
