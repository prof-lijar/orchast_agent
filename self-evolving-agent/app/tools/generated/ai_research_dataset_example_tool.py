import json

def ai_research_dataset_example_tool() -> dict:
    """
    Provides a sample JSON array representing typical AI model performance 
    results (e.g., accuracy, loss, F1-score) for testing data analysis tools.

    Args:
        None

    Returns:
        A dictionary containing the sample dataset as a JSON string
        under the key 'sample_dataset_json'.
    """
    sample_data = [
        {
            "model_id": "BERT_Small_A",
            "task": "Sentiment Analysis",
            "accuracy": 0.885,
            "f1_score": 0.879,
            "loss": 0.152,
            "epochs": 10
        },
        {
            "model_id": "RoBERTa_Base_B",
            "task": "Sentiment Analysis",
            "accuracy": 0.912,
            "f1_score": 0.908,
            "loss": 0.098,
            "epochs": 15
        },
        {
            "model_id": "GPT2_Medium_C",
            "task": "Text Generation",
            "accuracy": None,  # Accuracy not applicable for all tasks
            "f1_score": 0.755,
            "loss": 0.351,
            "epochs": 8
        },
        {
            "model_id": "CNN_VGG16_D",
            "task": "Image Classification",
            "accuracy": 0.951,
            "f1_score": 0.950,
            "loss": 0.045,
            "epochs": 20
        },
        {
            "model_id": "ResNet50_E",
            "task": "Image Classification",
            "accuracy": 0.963,
            "f1_score": 0.962,
            "loss": 0.032,
            "epochs": 25
        },
        {
            "model_id": "XGBoost_F",
            "task": "Tabular Prediction",
            "accuracy": 0.850,
            "f1_score": 0.840,
            "loss": 0.180,
            "epochs": 50 # Proxy for iterations
        }
    ]

    return {
        "sample_dataset_json": json.dumps(sample_data, indent=2)
    }
