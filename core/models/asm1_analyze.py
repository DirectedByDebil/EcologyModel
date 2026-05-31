import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


class SimpleAnalyzer:
    """Анализ для упрощённой модели (S_bio, X, S_inert, O)"""
    
    @staticmethod
    def analyze_physical(sol, params, clar_results):
        t_days = sol.t / 24
        S_bio, X, S_inert, O = sol.y
        BOD_aer = S_bio + S_inert
        
        print("="*60)
        print("ФИЗИЧЕСКИ КОРРЕКТНАЯ МОДЕЛЬ АЭРОТЕНКА (simple)")
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
        print(f"  Активный ил (X): {X[-1]:.0f} мг/л")
        
        print(f"\n🧪 ПОСЛЕ ОТСТОЙНИКА:")
        print(f"  БПК финальный: {clar_results['BOD_final'][-1]:.1f} мг/л")
        print(f"  Удаление инертных: {clar_results['removal'][-1]*100:.0f}%")
        
        if clar_results['BOD_final'][-1] <= 20:
            print(f"\n✅ НОРМАТИВ 20 мг/л ДОСТИГНУТ")
        else:
            print(f"\n⚠️ НОРМАТИВ 20 мг/л НЕ ДОСТИГНУТ (превышение {clar_results['BOD_final'][-1]-20:.1f} мг/л)")
    
    @staticmethod
    def analyze_bod(sol):
        t_days = sol.t
        S_bio, X, S_inert, O = sol.y
        BOD_aer = S_bio + S_inert
        
        BOD_end = BOD_aer[-1]
        BOD_start = BOD_aer[0]
        threshold = BOD_start - 0.95 * (BOD_start - BOD_end)
        
        idx = np.where(BOD_aer <= threshold)[0]
        if len(idx) > 0:
            time_to_95 = t_days[idx[0]]
            print(f"\n⏱️ Время достижения 95% очистки: {time_to_95:.1f} дней")
            return time_to_95
        print("\n⚠️ Стационарный режим не достигнут")
        return None
    
    @staticmethod
    def sensitivity_analysis(base_params, model_func, clarifier_func, param_changes):
        results = []
        sol_base, _ = model_func(base_params)
        clar_base = clarifier_func(sol_base, base_params)
        bod_base = clar_base['BOD_final'][-1]
        x_base = clar_base['X'][-1]
        o_base = sol_base.y[3][-1]
        fm_base = clar_base['F_M'][-1]
        
        results.append({
            'Сценарий': 'Базовый', 'Изменённый параметр': '-',
            'БПК вых., мг/л': round(bod_base, 2), 'Δ БПК, мг/л': 0.0, 'Δ БПК, %': 0.0,
            'Ил X, мг/л': round(x_base, 0), 'DO, мг/л': round(o_base, 1),
            'F/M, кг/кг·сут': round(fm_base, 3), 'Статус (≤20)': '✅' if bod_base <= 20 else '❌'
        })
        
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
                results.append({
                    'Сценарий': name,
                    'Изменённый параметр': f"{changed_param} ({old_val:.2g} → {p[changed_param]:.2g})",
                    'БПК вых., мг/л': round(bod, 2), 'Δ БПК, мг/л': round(delta, 2),
                    'Δ БПК, %': round(delta_pct, 1), 'Ил X, мг/л': round(x_final, 0),
                    'DO, мг/л': round(o_final, 1), 'F/M, кг/кг·сут': round(fm, 3),
                    'Статус (≤20)': '✅' if bod <= 20 else '❌'
                })
            except Exception as e:
                results.append({'Сценарий': name, 'Изменённый параметр': f'{changed_param} (ошибка)',
                                'БПК вых., мг/л': None, 'Δ БПК, мг/л': None, 'Δ БПК, %': None,
                                'Ил X, мг/л': None, 'DO, мг/л': None, 'F/M, кг/кг·сут': None,
                                'Статус (≤20)': '❌'})
                print(f"Ошибка в {name}: {e}")
        
        df = pd.DataFrame(results)
        print("\n" + "="*80 + "\nАНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ (simple)\n" + "="*80)
        print(df.to_string(index=False))
        return df
    
    @staticmethod
    def computational_experiments(base_params, model_func, clarifier_func):
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
        bod_in = base_params['S_bio_in'] + base_params['S_inert_in']
        
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
                
                S_bio, X, S_inert, O = sol.y
                bod_aer = (S_bio + S_inert)[-1]
                o_final = O[-1]
                
                mu_last = (p['mu_max'] * (S_bio[-1] / (p['K_S'] + S_bio[-1])) *
                          (O[-1] / (p['K_O'] + O[-1])) * (1 - X[-1] / p['X_max']))
                
                eff = (bod_in - bod_final) / bod_in * 100 if bod_in > 0 else 0
                nedochistka = max(0, bod_final - 20)
                
                BOD_aer_full = S_bio + S_inert
                threshold = BOD_aer_full[0] - 0.95 * (BOD_aer_full[0] - BOD_aer_full[-1])
                idx = np.where(BOD_aer_full <= threshold)[0]
                time_stab = t_days[idx[0]] if len(idx) > 0 else None
                
                results.append({
                    'Сценарий': name, 'БПК вх., мг/л': round(bod_in, 1),
                    'БПК после аэротенка, мг/л': round(bod_aer, 1),
                    'БПК вых., мг/л': round(bod_final, 1), 'Эффективность, %': round(eff, 1),
                    'Недосчистка, мг/л': round(nedochistka, 1), 'Ил X, мг/л': round(x_final, 0),
                    'Вынос ила, мг/л': round(x_final_out, 1), 'Удаление инертных, %': round(removal, 1),
                    'F/M, кг/кг·сут': round(fm, 3), 'DO, мг/л': round(o_final, 1),
                    'μ, 1/день': round(mu_last, 3), 'Стабилизация, дни': round(time_stab, 1) if time_stab else '>30',
                    'Статус (≤20)': '✅' if bod_final <= 20 else '❌'
                })
            except Exception as e:
                print(f"Ошибка в {name}: {e}")
                results.append({'Сценарий': name, 'Ошибка': str(e)})
        
        df = pd.DataFrame(results)
        print("\n" + "="*80 + "\nВЫЧИСЛИТЕЛЬНЫЕ ЭКСПЕРИМЕНТЫ (simple)\n" + "="*80)
        print(df.to_string(index=False))
        return df


class NitriAnalyzer:
    """Анализ для модели с нитрификацией (S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O)"""
    
    @staticmethod
    def analyze_physical(sol, params, clar_results):
        t_days = sol.t / 24
        S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O = sol.y
        BOD_aer = S_bio + S_inert
        X_total = X_BH + X_BA
        
        print("="*60)
        print("ФИЗИЧЕСКИ КОРРЕКТНАЯ МОДЕЛЬ АЭРОТЕНКА (with_nitri)")
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
        print(f"  Общая биомасса (X_BH+X_BA): {X_total[-1]:.0f} мг/л")
        print(f"    - Гетеротрофы (X_BH): {X_BH[-1]:.0f} мг/л")
        print(f"    - Автотрофы (X_BA): {X_BA[-1]:.0f} мг/л")
        print(f"  Аммоний (S_NH): {S_NH[-1]:.1f} мг N/л")
        print(f"  Нитраты (S_NO): {S_NO[-1]:.1f} мг N/л")
        
        print(f"\n🧪 ПОСЛЕ ОТСТОЙНИКА:")
        print(f"  БПК финальный: {clar_results['BOD_final'][-1]:.1f} мг/л")
        print(f"  Удаление инертных: {clar_results['removal'][-1]*100:.0f}%")
        
        if clar_results['BOD_final'][-1] <= 20:
            print(f"\n✅ НОРМАТИВ 20 мг/л ДОСТИГНУТ")
        else:
            print(f"\n⚠️ НОРМАТИВ 20 мг/л НЕ ДОСТИГНУТ (превышение {clar_results['BOD_final'][-1]-20:.1f} мг/л)")
    
    @staticmethod
    def analyze_bod(sol):
        t_days = sol.t
        S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O = sol.y
        BOD_aer = S_bio + S_inert
        
        BOD_end = BOD_aer[-1]
        BOD_start = BOD_aer[0]
        threshold = BOD_start - 0.95 * (BOD_start - BOD_end)
        
        idx = np.where(BOD_aer <= threshold)[0]
        if len(idx) > 0:
            time_to_95 = t_days[idx[0]]
            print(f"\n⏱️ Время достижения 95% очистки: {time_to_95:.1f} дней")
            return time_to_95
        print("\n⚠️ Стационарный режим не достигнут")
        return None
    
    @staticmethod
    def sensitivity_analysis(base_params, model_func, clarifier_func, param_changes):
        results = []
        sol_base, _ = model_func(base_params)
        clar_base = clarifier_func(sol_base, base_params)
        bod_base = clar_base['BOD_final'][-1]
        x_base = (sol_base.y[1] + sol_base.y[3])[-1]  # X_BH + X_BA
        o_base = sol_base.y[6][-1]
        fm_base = clar_base['F_M'][-1]
        nh_base = sol_base.y[4][-1]
        no_base = sol_base.y[5][-1]
        
        results.append({
            'Сценарий': 'Базовый', 'Изменённый параметр': '-',
            'БПК вых., мг/л': round(bod_base, 2), 'Δ БПК, мг/л': 0.0, 'Δ БПК, %': 0.0,
            'Ил X, мг/л': round(x_base, 0), 'DO, мг/л': round(o_base, 1),
            'NH4, мг N/л': round(nh_base, 1), 'NO3, мг N/л': round(no_base, 1),
            'F/M, кг/кг·сут': round(fm_base, 3), 'Статус (≤20)': '✅' if bod_base <= 20 else '❌'
        })
        
        for name, changes in param_changes.items():
            p = base_params.copy()
            changed_param = list(changes.keys())[0]
            old_val = p[changed_param]
            p.update(changes)
            try:
                sol, _ = model_func(p)
                clar = clarifier_func(sol, p)
                bod = clar['BOD_final'][-1]
                x_final = (sol.y[1] + sol.y[3])[-1]
                o_final = sol.y[6][-1]
                fm = clar['F_M'][-1]
                nh_final = sol.y[4][-1]
                no_final = sol.y[5][-1]
                delta = bod - bod_base
                delta_pct = (delta / bod_base) * 100 if bod_base != 0 else 0
                results.append({
                    'Сценарий': name,
                    'Изменённый параметр': f"{changed_param} ({old_val:.2g} → {p[changed_param]:.2g})",
                    'БПК вых., мг/л': round(bod, 2), 'Δ БПК, мг/л': round(delta, 2),
                    'Δ БПК, %': round(delta_pct, 1), 'Ил X, мг/л': round(x_final, 0),
                    'DO, мг/л': round(o_final, 1), 'NH4, мг N/л': round(nh_final, 1),
                    'NO3, мг N/л': round(no_final, 1), 'F/M, кг/кг·сут': round(fm, 3),
                    'Статус (≤20)': '✅' if bod <= 20 else '❌'
                })
            except Exception as e:
                results.append({'Сценарий': name, 'Изменённый параметр': f'{changed_param} (ошибка)',
                                'БПК вых., мг/л': None, 'Δ БПК, мг/л': None, 'Δ БПК, %': None,
                                'Ил X, мг/л': None, 'DO, мг/л': None, 'NH4, мг N/л': None,
                                'NO3, мг N/л': None, 'F/M, кг/кг·сут': None, 'Статус (≤20)': '❌'})
                print(f"Ошибка в {name}: {e}")
        
        df = pd.DataFrame(results)
        print("\n" + "="*80 + "\nАНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ (with_nitri)\n" + "="*80)
        print(df.to_string(index=False))
        return df
    
    @staticmethod
    def computational_experiments(base_params, model_func, clarifier_func):
        scenarios = {
            'Базовый': base_params.copy(),
            'Высокая нагрузка': {**base_params, 'S_bio_in': base_params['S_bio_in'] * 1.5},
            'Низкая температура': {**base_params, 'mu_max_H': base_params['mu_max_H'] * 0.7},
            'Увеличенный расход': {**base_params, 'Q': base_params['Q'] * 2},
            'Снижение рециркуляции': {**base_params, 'r': base_params['r'] * 0.7},
            'Слабая аэрация': {**base_params, 'kLa': base_params['kLa'] * 0.7},
            'Повышенная рециркуляция': {**base_params, 'r': min(1.0, base_params['r'] * 1.3)},
            'Усиленная аэрация': {**base_params, 'kLa': base_params['kLa'] * 1.5},
        }
        
        results = []
        bod_in = base_params['S_bio_in'] + base_params['S_inert_in']
        
        for name, p in scenarios.items():
            try:
                sol, _ = model_func(p)
                t_days = sol.t
                clar = clarifier_func(sol, p)
                bod_final = clar['BOD_final'][-1]
                removal = clar['removal'][-1] * 100
                fm = clar['F_M'][-1]
                x_final_out = clar['X_final'][-1]
                
                S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O = sol.y
                bod_aer = (S_bio + S_inert)[-1]
                o_final = O[-1]
                x_final = X_BH[-1] + X_BA[-1]
                nh_final = S_NH[-1]
                no_final = S_NO[-1]
                
                mu_H_last = (p['mu_max_H'] * (S_bio[-1] / (p['K_S'] + S_bio[-1])) *
                            (O[-1] / (p['K_OH'] + O[-1])) * (1 - (X_BH[-1] + X_BA[-1]) / p['X_max']))
                mu_A_last = (p['mu_max_A'] * (S_NH[-1] / (p['K_NH'] + S_NH[-1])) *
                            (O[-1] / (p['K_OA'] + O[-1])) * (1 - (X_BH[-1] + X_BA[-1]) / p['X_max']))
                
                eff = (bod_in - bod_final) / bod_in * 100 if bod_in > 0 else 0
                nedochistka = max(0, bod_final - 20)
                
                BOD_aer_full = S_bio + S_inert
                threshold = BOD_aer_full[0] - 0.95 * (BOD_aer_full[0] - BOD_aer_full[-1])
                idx = np.where(BOD_aer_full <= threshold)[0]
                time_stab = t_days[idx[0]] if len(idx) > 0 else None
                
                results.append({
                    'Сценарий': name, 'БПК вх., мг/л': round(bod_in, 1),
                    'БПК после аэротенка, мг/л': round(bod_aer, 1),
                    'БПК вых., мг/л': round(bod_final, 1), 'Эффективность, %': round(eff, 1),
                    'Недосчистка, мг/л': round(nedochistka, 1), 'Ил X, мг/л': round(x_final, 0),
                    'Вынос ила, мг/л': round(x_final_out, 1), 'Удаление инертных, %': round(removal, 1),
                    'NH4, мг N/л': round(nh_final, 1), 'NO3, мг N/л': round(no_final, 1),
                    'F/M, кг/кг·сут': round(fm, 3), 'DO, мг/л': round(o_final, 1),
                    'μ_H, 1/день': round(mu_H_last, 3), 'μ_A, 1/день': round(mu_A_last, 3),
                    'Стабилизация, дни': round(time_stab, 1) if time_stab else '>30',
                    'Статус (≤20)': '✅' if bod_final <= 20 else '❌'
                })
            except Exception as e:
                print(f"Ошибка в {name}: {e}")
                results.append({'Сценарий': name, 'Ошибка': str(e)})
        
        df = pd.DataFrame(results)
        print("\n" + "="*80 + "\nВЫЧИСЛИТЕЛЬНЫЕ ЭКСПЕРИМЕНТЫ (with_nitri)\n" + "="*80)
        print(df.to_string(index=False))
        return df


# ============= ДИСПЕТЧЕР =============

def analyze_model(sol, params, clar_results, model_name="simple"):
    """Основной диспетчер анализа"""
    if model_name == "simple":
        SimpleAnalyzer.analyze_physical(sol, params, clar_results)
        SimpleAnalyzer.analyze_bod(sol)
    elif model_name == "with_nitri":
        NitriAnalyzer.analyze_physical(sol, params, clar_results)
        NitriAnalyzer.analyze_bod(sol)
    else:
        print(f"Неизвестная модель: {model_name}")


def sensitivity_analysis(base_params, model_func, clarifier_func, param_changes, model_name="simple"):
    if model_name == "simple":
        return SimpleAnalyzer.sensitivity_analysis(base_params, model_func, clarifier_func, param_changes)
    elif model_name == "with_nitri":
        return NitriAnalyzer.sensitivity_analysis(base_params, model_func, clarifier_func, param_changes)
    else:
        print(f"Неизвестная модель: {model_name}")
        return None


def computational_experiments(base_params, model_func, clarifier_func, model_name="simple"):
    if model_name == "simple":
        return SimpleAnalyzer.computational_experiments(base_params, model_func, clarifier_func)
    elif model_name == "with_nitri":
        return NitriAnalyzer.computational_experiments(base_params, model_func, clarifier_func)
    else:
        print(f"Неизвестная модель: {model_name}")
        return None


def calculate_metrics(bod_model, bod_actual):
    if len(bod_model) != len(bod_actual):
        print("Ошибка: массивы разной длины")
        return None
    r2 = r2_score(bod_actual, bod_model)
    rmse = np.sqrt(mean_squared_error(bod_actual, bod_model))
    mae = mean_absolute_error(bod_actual, bod_model)
    print(f"R² = {r2:.3f}\nRMSE = {rmse:.2f} мг/л\nMAE = {mae:.2f} мг/л")
    return {'R2': r2, 'RMSE': rmse, 'MAE': mae}

