.PHONY: install smoke test clean all

install:
	pip install -e .

smoke:
	@echo "Running smoke tests with mock adapters..."
	MOCK_MODE=true python -m phi_eval.run --config phi_eval/configs/smoke.yaml
	MOCK_MODE=true python -m di_eval.run --config di_eval/configs/smoke.yaml
	MOCK_MODE=true python -m ot_bench.run --config ot_bench/configs/smoke.yaml
	@echo "✅ All smoke tests passed"

test:
	pytest tests/ -v

clean:
	rm -rf outputs/phi/* outputs/di/* outputs/ot/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

all: install smoke
	@echo "🎉 Full validation complete"
