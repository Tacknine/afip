import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent

REPORTS_DIR = BASE_DIR / "reports"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

TRAINING_REPORT = REPORTS_DIR / "training_report.json"
EVALUATION_REPORT = REPORTS_DIR / "evaluation_report.json"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_regression(metrics):
    mae = metrics.get("mae_kg")
    rmse = metrics.get("rmse_kg")
    r2 = metrics.get("r2")
    baseline_mae = metrics.get("baseline_mae_kg")

    result = {
        "metrics_available": True,
        "baseline_comparison": {},
        "quality_checks": [],
        "recommendation": "REVIEW"
    }

    values = [mae, rmse, r2, baseline_mae]

    if any(value is None for value in values):
        result["metrics_available"] = False
        result["recommendation"] = "INSUFFICIENT_METRICS"
        return result

    if baseline_mae <= 0:
        result["metrics_available"] = False
        result["recommendation"] = "INVALID_BASELINE"
        return result

    improvement = (
        (baseline_mae - mae) / baseline_mae
    ) * 100

    result["baseline_comparison"] = {
        "baseline_mae": baseline_mae,
        "model_mae": mae,
        "improvement_percent": round(improvement, 4)
    }

    # MAE must be better than baseline.
    if mae < baseline_mae:
        result["quality_checks"].append({
            "check": "baseline_comparison",
            "status": "passed"
        })
    else:
        result["quality_checks"].append({
            "check": "baseline_comparison",
            "status": "failed"
        })

    # R2 close to zero indicates weak explanatory power.
    if r2 >= 0.50:
        r2_status = "good"
    elif r2 >= 0.10:
        r2_status = "moderate"
    else:
        r2_status = "weak"

    result["quality_checks"].append({
        "check": "r2_score",
        "value": r2,
        "status": r2_status
    })

    # MAE improvement should be meaningful.
    if improvement >= 10:
        improvement_status = "good"
    elif improvement > 0:
        improvement_status = "marginal"
    else:
        improvement_status = "failed"

    result["quality_checks"].append({
        "check": "improvement_over_baseline",
        "value_percent": round(improvement, 4),
        "status": improvement_status
    })

    if mae < baseline_mae and r2 >= 0.10 and improvement >= 10:
        result["recommendation"] = "PROMISING_REQUIRES_FURTHER_VALIDATION"
    elif mae < baseline_mae:
        result["recommendation"] = "WEAK_MODEL_REQUIRES_IMPROVEMENT"
    else:
        result["recommendation"] = "DO_NOT_USE"

    return result


def evaluate_all():
    training = load_json(TRAINING_REPORT)

    output = {
        "platform": "AFIP",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "models": {}
    }

    for model_name, training_result in training.get(
        "models", {}
    ).items():

        model_result = {
            "training_status": training_result.get("status"),
            "evaluation_status": "not_evaluated"
        }

        metrics = training_result.get("metrics")

        if metrics:
            model_result["metrics"] = metrics
            model_result["evaluation"] = evaluate_regression(
                metrics
            )
            model_result["evaluation_status"] = "completed"

        else:
            model_result["reason"] = training_result.get(
                "reason",
                "No evaluation metrics available."
            )

        output["models"][model_name] = model_result

    with open(
        EVALUATION_REPORT,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("=" * 75)
    print("AFIP MODEL EVALUATION")
    print("=" * 75)

    for name, result in output["models"].items():
        print(f"\nMODEL: {name.upper()}")
        print(f"Training status: {result['training_status']}")

        if "evaluation" in result:
            evaluation = result["evaluation"]

            print(
                "Recommendation:",
                evaluation["recommendation"]
            )

            comparison = evaluation.get(
                "baseline_comparison", {}
            )

            if comparison:
                print(
                    "MAE improvement:",
                    comparison["improvement_percent"],
                    "%"
                )

            for check in evaluation.get(
                "quality_checks", []
            ):
                print(
                    check["check"],
                    "=>",
                    check["status"]
                )
        else:
            print(
                "Reason:",
                result.get("reason")
            )

    print("\nEvaluation report:", EVALUATION_REPORT)
    print("EVALUATION COMPLETED.")

    return output


if __name__ == "__main__":
    evaluate_all()
