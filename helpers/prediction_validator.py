
def validate_prediction_response(response):
    """Validate and fix prediction response format"""
    if response is None:
        return {"error": "Prediction returned None"}
    
    if isinstance(response, (int, float)):
        return {
            "prediction": float(response),
            "confidence": 0.5,
            "method": "scalar_fallback"
        }
    
    if isinstance(response, dict):
        if "error" in response:
            return response
        
        # Standardize prediction format
        prediction = response.get("prediction", response.get("sentiment_score", 0.0))
        confidence = response.get("confidence", response.get("avg_confidence", 0.5))
        
        return {
            "prediction": float(prediction),
            "confidence": float(confidence),
            "method": "dict_normalized",
            "original_keys": list(response.keys())
        }
    
    return {"error": f"Unexpected response type: {type(response)}"}
