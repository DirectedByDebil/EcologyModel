import asm1_params as ap
import asm1_model as am
import asm1_view as av
import asm1_analyze as aa
import os
from pandas import DataFrame

city_params = ap.get_city_params('vlg')

def save_tertiary_treatment(all_tt, model=""):
    df_tertiary = DataFrame([
        {
            'method': item['method'],
            'bod_out': item['data']['bod_out'],
            'ss_out': item['data']['ss_out'],
            'eff_bod': item['data']['eff_bod'],
            'eff_ss': item['data']['eff_ss'],
            'fm_ratio': item['data']['fm_ratio'],
            'ji': item['data'].get('ji', 'N/A')
        }
        for item in all_tt
    ])

    path_tertiary = os.path.join("results", model, f"tertiary_treatment_{model}.csv")
    os.makedirs(os.path.dirname(path_tertiary), exist_ok=True)
    df_tertiary.to_csv(path_tertiary, index=False)


def benchmark_model (city_params: dict, ctx = None):

    if ctx is None:
        print("no ctx specified - skip benchmark...")
        return

    sol = None
    params = None
    clar = None
    df_sens = None
    comp_exp = None

    tertiary_methods=[
        'sand_filter',
        'disc_filter',
        'membrane',
        'carbon_filter',
        'coagulation_filtration'
    ]

    param_changes = {
        'Высокая нагрузка (+50%)': {'S_bio_in': city_params['S_bio_in'] * 1.5},
        'Низкая температура': {'mu_max': city_params['mu_max'] * 0.7},
        'Увеличенный расход (HRT/2)': {'Q': city_params['Q'] * 2},
        'Снижение рециркуляции (-30%)': {'r': city_params['r'] * 0.7},
        'Слабая аэрация (-30%)': {'kLa': city_params['kLa'] * 0.7},
    }

    model = ctx["model"]

    match (model):
        case 'simple':
            sol, params = am.aeration_tank_physical(city_params)
            params['S_in'] = params['S_bio_in'] + params['S_inert_in']

            clar = am.secondary_clarifier_physical(sol, params)

            df_sens = aa.sensitivity_analysis(city_params, am.aeration_tank_physical, am.secondary_clarifier_physical, param_changes, model_name=model)

            comp_exp = aa.computational_experiments(city_params, am.aeration_tank_physical, am.secondary_clarifier_physical, model_name=model)

        case 'with_nitri':
            sol, params = am.aeration_tank_physical_with_nitri(city_params)
            params['S_in'] = params['S_bio_in'] + params['S_inert_in']

            clar = am.secondary_clarifier_with_nitri(sol, params)

            df_sens = aa.sensitivity_analysis(city_params, am.aeration_tank_physical_with_nitri, am.secondary_clarifier_with_nitri, param_changes, model_name=model)

            comp_exp = aa.computational_experiments(city_params, am.aeration_tank_physical_with_nitri, am.secondary_clarifier_with_nitri, model_name=model)

        case _:
            print('no model selected')
            return 0

    all_tt = []

    for method in tertiary_methods:
        tt = am.tertiary_treatment(params, clar, method)
        all_tt.append({
            "method": method,
            "data": tt
        })

    allowed_methods = ['membrane']
    filtered_tt = [item for item in all_tt if item['method'] in allowed_methods]

    ctx['tertiary_treatment'] = filtered_tt

    av.plot_results_v2(sol, params, clar, ctx)

    aa.analyze_model(sol, params, clar, model_name=model)

    save_tertiary_treatment(all_tt, model)

    path = os.path.join("results", model, f"sensitivity_analysis_{model}.csv")
    print(path)
    df_sens.to_csv(path, index=False)

    path = os.path.join("results", model, f"computer_experiments_{model}.csv")
    print(path)
    comp_exp.to_csv(path, index=False)



