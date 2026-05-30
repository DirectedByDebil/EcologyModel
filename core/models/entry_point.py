import asm1_params as ap
import asm1_model as am
import asm1_analyze as aa

city_params = ap.get_city_params('vlg')

sol, params = am.aeration_tank_physical(city_params)
params['S_in'] = params['S_bio_in'] + params['S_inert_in']

clar = am.secondary_clarifier_physical(sol, params)

#av.plot_results_v2(sol, params, clar)

#aa.analyze_physical(sol, params, clar)
#aa.analyze_bod(sol)

param_changes = {
    'Высокая нагрузка (+50%)': {'S_bio_in': city_params['S_bio_in'] * 1.5},
    'Низкая температура': {'mu_max': city_params['mu_max'] * 0.7},
    'Увеличенный расход (HRT/2)': {'Q': city_params['Q'] * 2},
    'Снижение рециркуляции (-30%)': {'r': city_params['r'] * 0.7},
    'Слабая аэрация (-30%)': {'kLa': city_params['kLa'] * 0.7},
}
df_sens = aa.sensitivity_analysis(city_params, am.aeration_tank_physical, am.secondary_clarifier_physical, param_changes)
df_sens.to_csv('sensitivity_analysis.csv', index=False)

comp_exp = aa.computational_experiments(city_params, am.aeration_tank_physical, am.secondary_clarifier_physical)
comp_exp.to_csv('computer_experiments.csv', index=False)

