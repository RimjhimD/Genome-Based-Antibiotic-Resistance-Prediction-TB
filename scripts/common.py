"""Settings shared by the training scripts."""
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier

DRUGS = ["INH", "RIF", "EMB", "ETH", "LEV", "MXF", "KAN", "AMI"]
SEED = 0


def models(pos_weight):
    return {
        "LR": LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000,
                                 solver="liblinear"),
        "RF": RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                     class_weight="balanced", n_jobs=-1, random_state=SEED),
        "XGB": XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.1,
                             subsample=0.8, colsample_bytree=0.8, scale_pos_weight=pos_weight,
                             tree_method="hist", n_jobs=-1, random_state=SEED, verbosity=0),
        "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), alpha=1e-3, max_iter=200,
                             early_stopping=True, random_state=SEED),
    }
