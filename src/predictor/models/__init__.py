from predictor.models.base import EXTRA_COLUMNS, PREDICTION_COLUMNS, LeakageError, MatchModel
from predictor.models.blend import BlendModel
from predictor.models.dixon_coles import DixonColesModel
from predictor.models.elo import EloModel

MODELS = {EloModel.name: EloModel, DixonColesModel.name: DixonColesModel, BlendModel.name: BlendModel}


def get_model(name: str, **overrides) -> MatchModel:
    return MODELS[name](**overrides)
