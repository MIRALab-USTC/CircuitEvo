from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
import torch

app = Flask(__name__)

# Load your model
model_path = "./eoh/src/eoh/local_model/global_step_16_huggingface"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path).cuda().eval()

@app.route("/completions", methods=["POST"])
def complete():
    data = request.json
    prompt = data.get("prompt")
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=128,
        do_sample=True,
        top_k=50,
        top_p=0.9,
        temperature=1.0,
    )
    result = tokenizer.decode(output[0], skip_special_tokens=True)
    return jsonify({"text": result})

if __name__ == "__main__":
    app.run(port=11012)
