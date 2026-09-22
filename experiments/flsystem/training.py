import subprocess
import time
from pathlib import Path


def dataset(seed, samples):
    import torch
    generator = torch.Generator().manual_seed(seed)
    features = torch.randn(samples, 5, generator=generator)
    teacher = torch.tensor([1.2, -0.9, 0.6, 0.3, -0.5])
    labels = (features @ teacher + 0.15 * torch.randn(samples, generator=generator) > 0).float()
    return features, labels


def train_client(task):
    import torch
    torch.set_num_threads(1)
    started = time.perf_counter()
    features, labels = dataset(task["seed"] + task["client_index"], 48)
    model = torch.nn.Linear(5, 1)
    base = torch.tensor(task["model"], dtype=torch.float32)
    with torch.no_grad():
        model.weight.copy_(base[:5].reshape(1, 5))
        model.bias.copy_(base[5:])
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    generator = torch.Generator().manual_seed(task["seed"] + task["client_index"] + 10000)
    for _ in range(task["steps"]):
        indices = torch.randperm(len(labels), generator=generator)[:16]
        optimizer.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(
            model(features[indices]).flatten(), labels[indices])
        loss.backward()
        optimizer.step()
    trained = torch.cat([model.weight.detach().flatten(), model.bias.detach()])
    coefficients = torch.round((trained - base).clamp(-0.25, 0.25) * task["scale"]).to(torch.int64).tolist()
    encrypted = subprocess.run([task["binary"]], input=json_line({
        "Operation": "encrypt", "Public": task["public"], "Values": coefficients,
    }), text=True, capture_output=True, check=True, timeout=30)
    reference = Path(task["reference"])
    reference.write_text(json_line(coefficients, newline=False))
    reference.chmod(0o600)
    return {"sid": task["sid"], "client": str(task["client_index"]),
            "update_id": task["update_id"], "base_version": task["base_version"],
            "ciphertext": json_load(encrypted.stdout),
            "training_seconds": time.perf_counter() - started}


def json_line(value, newline=True):
    import json
    return json.dumps(value) + ("\n" if newline else "")


def json_load(value):
    import json
    return json.loads(value)
