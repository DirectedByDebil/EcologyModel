import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def analyze_physical(sol, params, clar_results):
    """
    Анализ физической модели
    """
    t_days = sol.t / 24
    S_bio, X, S_inert, O = sol.y
    BOD_aer = S_bio + S_inert
    
    print("="*60)
    print("ФИЗИЧЕСКИ КОРРЕКТНАЯ МОДЕЛЬ АЭРОТЕНКА")
    print("="*60)
    
    print(f"\n📊 ПАРАМЕТРЫ РЕАКТОРА:")
    print(f"  Объём: {params['V']} м³")
    print(f"  Расход: {params['Q']} м³/ч")
    print(f"  Время удержания (HRT): {params['V']/params['Q']:.1f} ч = {(params['V']/params['Q'])/24:.2f} дня")
    print(f"  Рециркуляция: {params['r']*100:.0f}%")
    
    print(f"\n📈 ДИНАМИКА:")
    print(f"  БПК на входе: {BOD_aer[0]:.1f} мг/л")
    print(f"  БПК через 1 день: {BOD_aer[np.argmin(np.abs(t_days-1))]:.1f} мг/л")
    print(f"  БПК через 3 дня: {BOD_aer[np.argmin(np.abs(t_days-3))]:.1f} мг/л")
    print(f"  БПК через 7 дней: {BOD_aer[np.argmin(np.abs(t_days-7))]:.1f} мг/л")
    print(f"  БПК стационар: {BOD_aer[-1]:.1f} мг/л")
    
    print(f"\n🧪 ПОСЛЕ ОТСТОЙНИКА:")
    print(f"  БПК финальный: {clar_results['BOD_final'][-1]:.1f} мг/л")
    print(f"  Удаление инертных: {clar_results['removal'][-1]*100:.0f}%")
    
    # Соответствие нормативу
    if clar_results['BOD_final'][-1] <= 20:
        print(f"\n✅ НОРМАТИВ 20 мг/л ДОСТИГНУТ")
    else:
        print(f"\n⚠️ НОРМАТИВ 20 мг/л НЕ ДОСТИГНУТ (превышение {clar_results['BOD_final'][-1]-20:.1f} мг/л)")
    

def analyze_bod (sol):

    # Проверка времени стабилизации
    t_days = sol.t
    BOD_aer = sol.y[0] + sol.y[2]

    # Находим, когда БПК достигает 95% от стационара
    BOD_end = BOD_aer[-1]
    BOD_start = BOD_aer[0]
    threshold = BOD_start - 0.95 * (BOD_start - BOD_end)

    idx = np.where(BOD_aer <= threshold)[0]
    if len(idx) > 0:
        time_to_95 = t_days[idx[0]]
        print(f"\n⏱️ Время достижения 95% очистки: {time_to_95:.1f} дней")


def sensitivity_analysis(base_params, model_func, clarifier_func, param_changes):
    """
    Анализ чувствительности: изменение одного параметра за раз.
    
    Параметры:
        base_params - словарь с базовыми параметрами
        model_func - функция модели аэротенка (sol, params)
        clarifier_func - функция отстойника
        param_changes - словарь {название_сценария: {параметр: новое_значение}}
    
    Возвращает:
        pandas DataFrame с результатами
    """
    results = []
    
    # Базовый расчёт
    sol_base, _ = model_func(base_params)
    clar_base = clarifier_func(sol_base, base_params)
    bod_base = clar_base['BOD_final'][-1]
    x_base = clar_base['X'][-1]
    o_base = sol_base.y[3][-1]
    fm_base = clar_base['F_M'][-1]
    
    results.append({
        'Сценарий': 'Базовый',
        'Изменённый параметр': '-',
        'БПК вых., мг/л': round(bod_base, 2),
        'Δ БПК, мг/л': 0.0,
        'Δ БПК, %': 0.0,
        'Ил X, мг/л': round(x_base, 0),
        'DO, мг/л': round(o_base, 1),
        'F/M, кг/кг·сут': round(fm_base, 3),
        'Статус (≤20)': '✅' if bod_base <= 20 else '❌'
    })
    
    # Расчёт для каждого сценария
    for name, changes in param_changes.items():
        p = base_params.copy()
        changed_param = list(changes.keys())[0]
        old_val = p[changed_param]
        p.update(changes)
        
        try:
            sol, _ = model_func(p)
            clar = clarifier_func(sol, p)
            bod = clar['BOD_final'][-1]
            x_final = clar['X'][-1]
            o_final = sol.y[3][-1]
            fm = clar['F_M'][-1]
            
            delta = bod - bod_base
            delta_pct = (delta / bod_base) * 100 if bod_base != 0 else 0
            status = '✅' if bod <= 20 else '❌'

            results.append({
                'Сценарий': name,
                'Изменённый параметр': f"{changed_param} ({old_val:.2g} → {p[changed_param]:.2g})",
                'БПК вых., мг/л': round(bod, 2),
                'Δ БПК, мг/л': round(delta, 2),
                'Δ БПК, %': round(delta_pct, 1),
                'Ил X, мг/л': round(x_final, 0),
                'DO, мг/л': round(o_final, 1),
                'F/M, кг/кг·сут': round(fm, 3),
                'Статус (≤20)': status
            })

        except Exception as e:
            results.append({
                'Сценарий': name,
                'Изменённый параметр': f'{changed_param} (ошибка)',
                'БПК вых., мг/л': None,
                'Δ БПК, мг/л': None,
                'Δ БПК, %': None,
                'Ил X, мг/л': None,
                'DO, мг/л': None,
                'F/M, кг/кг·сут': None,
                'Статус (≤20)': '❌'
            })
            print(f"Ошибка в сценарии {name}: {e}")
    
    df = pd.DataFrame(results)
    print("\n" + "="*80)
    print("АНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ")
    print("="*80)
    print(df.to_string(index=False))
    return df


def computational_experiments(base_params, model_func, clarifier_func):
    """
    Проведение вычислительных экспериментов для разных сценариев.
    Возвращает DataFrame с результатами.
    """
    scenarios = {
        'Базовый': base_params.copy(),
        'Высокая нагрузка': {**base_params, 'S_bio_in': base_params['S_bio_in'] * 1.5},
        'Низкая температура': {**base_params, 'mu_max': base_params['mu_max'] * 0.7},
        'Увеличенный расход': {**base_params, 'Q': base_params['Q'] * 2},
        'Снижение рециркуляции': {**base_params, 'r': base_params['r'] * 0.7},
        'Слабая аэрация': {**base_params, 'kLa': base_params['kLa'] * 0.7},
        'Повышенная рециркуляция': {**base_params, 'r': min(1.0, base_params['r'] * 1.3)},
        'Усиленная аэрация': {**base_params, 'kLa': base_params['kLa'] * 1.5},
    }
    
    results = []
    
    for name, p in scenarios.items():
        try:
            sol, _ = model_func(p)
            t_days = sol.t
            clar = clarifier_func(sol, p)
            
            bod_final = clar['BOD_final'][-1]
            x_final = clar['X'][-1]
            removal = clar['removal'][-1] * 100
            fm = clar['F_M'][-1]
            x_final_out = clar['X_final'][-1]
            
            # Достаём показатели из решения
            S_bio, X, S_inert, O = sol.y
            bod_aer = (S_bio + S_inert)[-1]
            o_final = O[-1]
            
            # Расчёт удельной скорости роста на последнем шаге
            mu_last = (p['mu_max'] * 
                      (S_bio[-1] / (p['K_S'] + S_bio[-1])) * 
                      (O[-1] / (p['K_O'] + O[-1])) *
                      (1 - X[-1] / p['X_max']))
            
            bod_in = base_params['S_bio_in'] + base_params['S_inert_in']
            
            eff = (bod_in - bod_final) / bod_in * 100 if bod_in > 0 else 0
            nedochistka = max(0, bod_final - 20)
            status = '✅' if bod_final <= 20 else '❌'
            
            # Время стабилизации
            BOD_aer_full = S_bio + S_inert
            BOD_end = BOD_aer_full[-1]
            BOD_start = BOD_aer_full[0]
            threshold = BOD_start - 0.95 * (BOD_start - BOD_end)
            idx = np.where(BOD_aer_full <= threshold)[0]
            time_stab = t_days[idx[0]] if len(idx) > 0 else None

            results.append({
                'Сценарий': name,
                'БПК вх., мг/л': round(bod_in, 1),
                'БПК после аэротенка, мг/л': round(bod_aer, 1),
                'БПК вых., мг/л': round(bod_final, 1),
                'Эффективность, %': round(eff, 1),
                'Недосчистка, мг/л': round(nedochistka, 1),
                'Ил X, мг/л': round(x_final, 0),
                'Вынос ила, мг/л': round(x_final_out, 1),
                'Удаление инертных, %': round(removal, 1),
                'F/M, кг/кг·сут': round(fm, 3),
                'DO, мг/л': round(o_final, 1),
                'μ, 1/день': round(mu_last, 3),
                'Стабилизация, дни': round(time_stab, 1) if time_stab else '>30',
                'Статус (≤20)': status
            })

        except Exception as e:
            print(f"Ошибка в сценарии {name}: {e}")
            results.append({'Сценарий': name, 'Ошибка': str(e)})
    
    df = pd.DataFrame(results)
    print("\n" + "="*80)
    print("ВЫЧИСЛИТЕЛЬНЫЕ ЭКСПЕРИМЕНТЫ")
    print("="*80)
    print(df.to_string(index=False))
    return df

def calculate_metrics(bod_model, bod_actual):
    """
    bod_model - массив модельных значений БПК (на выходе)
    bod_actual - массив реальных замеров (те же дни)
    """
    r2 = r2_score(bod_actual, bod_model)
    rmse = np.sqrt(mean_squared_error(bod_actual, bod_model))
    mae = mean_absolute_error(bod_actual, bod_model)
    
    print(f"R² = {r2:.3f}")
    print(f"RMSE = {rmse:.2f} мг/л")
    print(f"MAE = {mae:.2f} мг/л")
    
    return {'R2': r2, 'RMSE': rmse, 'MAE': mae}

