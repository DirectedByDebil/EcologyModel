import asm1_params as ap
import asm1_model as am
import asm1_view as av
import asm1_analyze as aa
import asm1_benchmark as ab

city_params = ap.get_city_params('vlg')

ctxs = [{"model": "simple"},{"model": "with_nitri"}]

for ctx in ctxs:

    model = ctx["model"]

    print("="*60)
    print(f"Model: {model}")

    ab.benchmark_model(city_params, ctx)


