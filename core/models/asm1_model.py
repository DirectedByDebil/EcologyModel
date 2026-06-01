import numpy as np
from scipy.integrate import solve_ivp


def aeration_tank_physical(params=None):
    """
    Физически корректная модель аэротенка с явным объёмом и рециркуляцией
    """
    
    if params is None:
        params = {
            # Реактор (реальные размеры)
            'V': 5000,           # объём аэротенка, м³
            'Q': 1000,           # расход сточных вод, м³/ч
            
            # Рециркуляция
            'r': 0.5,            # коэффициент рециркуляции (50%)
            'X_r_max': 8000,     # макс. концентрация ила в рецикле, мг/л
            'eta': 0.3,          # удаление инертных в отстойнике (30%)
            
            # Кинетика (реалистичные значения)
            'Y': 0.67,           # урожайность, г/г
            'mu_max': 3.0/24,    # макс. скорость роста, 1/ч (3 1/день)
            'K_S': 100.0,        # константа полунасыщения по субстрату, мг/л
            'K_O': 0.5,          # константа по кислороду, мг/л
            'b': 0.1/24,         # скорость эндогенного дыхания, 1/ч
            'X_max': 8000,       # максимальная концентрация ила, мг/л
            'tau_adapt': 36,     # время адаптации бактерий, ч (1.5 дня)
            
            # Аэрация
            'kLa': 100/24,       # коэф. массопередачи кислорода, 1/ч
            'O_sat': 8.0,        # насыщение кислородом, мг/л
            
            # Входные концентрации (по факту)
            'S_bio_in': 150.0,   # биодеградируемый субстрат, мг/л
            'S_inert_in': 32.5,  # инертный субстрат, мг/л
            'X_in': 100.0,       # биомасса на входе, мг/л
            'O_in': 2.0,         # кислород на входе, мг/л
        }
    
    # Производные
    def derivatives(t, y, params):
        """
        y = [S_bio, X, S_inert, O]
        """
        S_bio, X, S_inert, O = y
        
        # Расходы
        Q = params['Q']
        Q_r = params['r'] * Q
        Q_w = 0.05 * Q  # удаление избыточного ила (5%)
        Q_total = Q + Q_r
        V = params['V']
        
        # Концентрации в рецикле (после отстойника)
        X_r = min(params['X_r_max'], X * 1.5)  # ил уплотняется
        S_bio_r = S_bio  # субстрат не меняется
        S_inert_r = S_inert * (1 - params['eta'])  # инертные частично удаляются
        O_r = O  # кислород не меняется
        
        # Адаптация бактерий (лаг-фаза)
        adapt = 1 - np.exp(-t / params['tau_adapt'])
        
        # Скорость роста с лимитами:
        # 1. По субстрату (Моно)
        # 2. По кислороду
        # 3. По плотности (логистическое торможение)
        # 4. По адаптации
        
        mu = (params['mu_max'] * 
              (S_bio / (params['K_S'] + S_bio)) * 
              (O / (params['K_O'] + O)) *
              (1 - X / params['X_max']) *
              adapt)
        
        # Балансовые уравнения
        
        # Субстрат
        dS_bio_dt = (Q * params['S_bio_in'] + Q_r * S_bio_r - Q_total * S_bio) / V \
                    - (mu / params['Y']) * X
        
        # Биомасса
        dX_dt = (Q * params['X_in'] + Q_r * X_r - (Q_total) * X) / V \
                + mu * X - params['b'] * X
        
        # Инертный субстрат
        dS_inert_dt = (Q * params['S_inert_in'] + Q_r * S_inert_r - Q_total * S_inert) / V
        
        # Кислород
        dO_dt = (Q * params['O_in'] + Q_r * O_r - Q_total * O) / V \
                + params['kLa'] * (params['O_sat'] - O) \
                - ((1 - params['Y']) / params['Y']) * mu * X
        
        return [dS_bio_dt, dX_dt, dS_inert_dt, dO_dt]
    
    # Начальные условия
    y0 = [
        params['S_bio_in'],
        3000.0,  # начальный ил, мг/л
        params['S_inert_in'],
        params['O_in']
    ]
    
    # Время моделирования (30 дней)
    t_span = (0, 30)
    t_eval = np.linspace(0, 30, 1000) 
    
    
    
    # Решение
    sol = solve_ivp(
        derivatives,
        t_span,
        y0,
        args=(params,),
        t_eval=t_eval,
        method='BDF',  # для жёстких систем
        rtol=1e-6
    )
    
    return sol, params

def secondary_clarifier_physical(sol, params):
    """
    Модель вторичного отстойника с учётом рециркуляции
    """
    S_bio = sol.y[0]
    X = sol.y[1]
    S_inert = sol.y[2]
    O = sol.y[3]
    t = sol.t
    
    # Параметры отстойника
    H = 3.0      # глубина, м
    v = 0.8      # скорость потока, м/ч
    k = 0.2      # эмпирический коэффициент
    
    # Эффективность осаждения (зависит от нагрузки)
    MLSS = X / 1000  # г/л
    #F_M = (params['S_bio_in'] * params['Q'] / params['V']) / MLSS  # нагрузка на ил
    #F_M = (params['S_bio_in'] * params['Q'] * 24 / params['V']) / MLSS / 1000
    Q_daily = params['Q'] * 24
    F_M = (params['S_bio_in'] * Q_daily / params['V']) / (X / 1000) / 1000
    
    # Эффективность удаления
    #removal = np.clip(0.2 + 0.1 * F_M, 0.25, 0.45)
    removal = np.clip(0.25 + 0.1 * F_M, 0.3, 0.4)  # было 0.2 + 0.1
    
    # Финальные концентрации
    S_inert_final = S_inert * (1 - removal)
    X_final = X * 0.01  # вынос ила 1%
    BOD_final = S_bio + S_inert_final
    
    return {
        't': t,
        'S_bio': S_bio,
        'X': X,
        'S_inert': S_inert,
        'S_inert_final': S_inert_final,
        'BOD_final': BOD_final,
        'X_final': X_final,
        'removal': removal,
        'F_M': F_M
    }


def aeration_tank_physical_with_nitri(params=None):
    """
    Модель аэротенка с нитрификацией и денитрификацией
    Переменные: [S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O]
    """
    
    if params is None:
        params = {
            # Реактор
            'V': 5000, 'Q': 1000, 'r': 0.57,
            'X_r_max': 8000, 'eta': 0.3,
            
            # Гетеротрофы
            'Y_H': 0.67, 'mu_max_H': 3.5/24, 'K_S': 120.0,
            'K_OH': 0.5, 'b_H': 0.15/24, 'X_max': 8000,
            
            # Автотрофы (нитрификация)
            'Y_A': 0.24, 'mu_max_A': 0.8/24, 'K_NH': 1.0,
            'K_OA': 0.4, 'b_A': 0.05/24,
            
            # Денитрификация
            'eta_g': 0.8, 'K_NO': 0.5,
            
            # Аэрация
            'kLa': 100/24, 'O_sat': 8.0,
            
            # Входные концентрации
            'S_bio_in': 150.0, 'S_inert_in': 32.5,
            'X_BH_in': 100.0, 'X_BA_in': 10.0,
            'S_NH_in': 30.0, 'S_NO_in': 0.5,
            'O_in': 2.0,
            
            # Адаптация
            'tau_adapt': 36,
        }
    
    def derivatives(t, y, p):
        S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O = y
        
        # Расходы
        Q = p['Q']; Q_r = p['r'] * Q; Q_total = Q + Q_r; V = p['V']
        
        # Рециркуляция
        X_BH_r = min(p['X_r_max'], X_BH * 1.5)
        X_BA_r = min(p['X_r_max'], X_BA * 1.5)
        S_bio_r = S_bio
        S_inert_r = S_inert * (1 - p['eta'])
        S_NH_r = S_NH
        S_NO_r = S_NO
        O_r = O
        
        # Адаптация
        adapt = 1 - np.exp(-t / p['tau_adapt'])
        
        # Лимит по плотности (для обеих биомасс)
        density_H = max(0, 1 - X_BH / p['X_max'])
        density_A = max(0, 1 - X_BA / (p['X_max'] / 2))
        
        # Скорость роста гетеротрофов (аэробная)
        mu_H = (p['mu_max_H'] * 
                (S_bio / (p['K_S'] + S_bio)) * 
                (O / (p['K_OH'] + O)) *
                density_H * adapt)
        
        # Скорость роста гетеротрофов (аноксидная, денитрификация)
        mu_H_anox = (p['mu_max_H'] * p['eta_g'] *
                     (S_bio / (p['K_S'] + S_bio)) *
                     (S_NO / (p['K_NO'] + S_NO)) *
                     (p['K_OH'] / (p['K_OH'] + O)) *
                     density_H * adapt)
        
        # Скорость роста автотрофов (нитрификация)
        mu_A = (p['mu_max_A'] *
                (S_NH / (p['K_NH'] + S_NH)) *
                (O / (p['K_OA'] + O)) *
                density_A * adapt)
        
        # ===== БАЛАНСОВЫЕ УРАВНЕНИЯ =====
        
        # Субстрат (биоразлагаемая органика)
        dS_bio = (Q * p['S_bio_in'] + Q_r * S_bio_r - Q_total * S_bio) / V \
                 - (mu_H / p['Y_H']) * X_BH - (mu_H_anox / p['Y_H']) * X_BH
        
        # Гетеротрофная биомасса
        dX_BH = (Q * p['X_BH_in'] + Q_r * X_BH_r - Q_total * X_BH) / V \
                + mu_H * X_BH + mu_H_anox * X_BH - p['b_H'] * X_BH
        
        # Инертный субстрат
        dS_inert = (Q * p['S_inert_in'] + Q_r * S_inert_r - Q_total * S_inert) / V
        
        # Автотрофная биомасса (нитрификаторы)
        dX_BA = (Q * p['X_BA_in'] + Q_r * X_BA_r - Q_total * X_BA) / V \
                + mu_A * X_BA - p['b_A'] * X_BA
        
        # Аммоний (потребляется гетеротрофами и автотрофами)
        dS_NH = (Q * p['S_NH_in'] + Q_r * S_NH_r - Q_total * S_NH) / V \
                - 0.086 * (mu_H + mu_H_anox) * X_BH \
                - (1 / p['Y_A']) * mu_A * X_BA
        
        # Нитраты (образуются автотрофами, потребляются гетеротрофами при денитрификации)
        dS_NO = (Q * p['S_NO_in'] + Q_r * S_NO_r - Q_total * S_NO) / V \
                + (1 - p['Y_A']) / (2.86 * p['Y_A']) * mu_A * X_BA \
                - (1 - p['Y_H']) / (2.86 * p['Y_H']) * mu_H_anox * X_BH
        
        # Кислород (потребляется гетеротрофами и автотрофами)
        dO = (Q * p['O_in'] + Q_r * O_r - Q_total * O) / V \
             + p['kLa'] * (p['O_sat'] - O) \
             - (1 - p['Y_H']) / p['Y_H'] * (mu_H + mu_H_anox) * X_BH \
             - (4.57 - p['Y_A']) / p['Y_A'] * mu_A * X_BA
        
        return [dS_bio, dX_BH, dS_inert, dX_BA, dS_NH, dS_NO, dO]
    
    # Начальные условия
    y0 = [
        params['S_bio_in'],
        params['X_BH_in'],
        params['S_inert_in'],
        params['X_BA_in'],
        params['S_NH_in'],
        params['S_NO_in'],
        params['O_in']
    ]
    
    t_span = (0, 30)
    t_eval = np.linspace(0, 30, 1000)
    
    sol = solve_ivp(derivatives, t_span, y0, args=(params,),
                    t_eval=t_eval, method='BDF', rtol=1e-6)
    
    return sol, params

def secondary_clarifier_with_nitri(sol, params):
    """
    Отстойник для модели с нитрификацией
    """
    S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O = sol.y
    
    Q_daily = params['Q'] * 24
    MLSS = (X_BH + X_BA) / 1000
    F_M = (params['S_bio_in'] * Q_daily / params['V']) / MLSS / 1000
    
    removal = np.clip(0.25 + 0.1 * F_M, 0.3, 0.4)
    
    S_inert_final = S_inert * (1 - removal)
    X_BH_final = X_BH * 0.01
    X_BA_final = X_BA * 0.01
    BOD_final = S_bio + S_inert_final
    
    return {
        't': sol.t,
        'S_bio': S_bio,
        'X_BH': X_BH,
        'S_inert': S_inert,
        'X_BA': X_BA,
        'S_NH': S_NH,
        'S_NO': S_NO,
        'O': O,
        'S_inert_final': S_inert_final,
        'BOD_final': BOD_final,
        'X_BH_final': X_BH_final,
        'X_BA_final': X_BA_final,
        'removal': removal,
        'F_M': F_M,
        'X_final': X_BH_final + X_BA_final,
        'X_BH_final': X_BH_final,
        'X_BA_final': X_BA_final 
    }


def tertiary_treatment(params, clar_results, method='sand_filter'):
    """
    Доочистка сточных вод после вторичного отстойника
    
    Параметры:
        sol - решение аэротенка
        params - параметры модели
        clar_results - результаты отстойника
        method - метод доочистки: 'sand_filter', 'disc_filter', 'membrane', 'carbon_filter', 'coagulation_filtration'
    
    Возвращает:
        словарь с результатами доочистки
    """
    
    # Извлекаем данные из отстойника
    bod_in = clar_results['BOD_final'][-1]  # БПК после отстойника, мг/л
    ss_in = clar_results['X_final'][-1]     # вынос ила (взвешенные вещества), мг/л
    fm_ratio = clar_results['F_M'][-1]      # иловая нагрузка F/M, кг/(кг·сут)
    
    # Иловый индекс (можно рассчитать приближённо по F/M)
    # При высоком F/M ил молодой и плохо оседает → индекс выше
    if 'Ji' in params:
        ji = params['Ji']
    else:
        # Эмпирическая зависимость: Ji = 50 + 100 * (fm_ratio - 0.3)
        ji = 50 + 100 * max(0, fm_ratio - 0.3)
        ji = min(ji, 200)  # ограничиваем
    
    # =========================================================
    # Расчёт эффективности в зависимости от метода
    # =========================================================
    
    if method == 'sand_filter':
        # Песчаный фильтр (медленный)
        # Эффективность зависит от концентрации взвеси и F/M
        base_eff_ss = 0.60
        # Коррекция по F/M: высокий F/M → хуже фильтрация
        fm_factor = 1.0 - (fm_ratio - 0.3) * 0.3
        fm_factor = max(0.7, min(1.0, fm_factor))
        eff_ss = base_eff_ss * fm_factor
        # БПК снижается пропорционально удалению взвеси
        eff_bod = eff_ss * 0.7 + 0.10
        
    elif method == 'disc_filter':
        # Дисковый фильтр (высокоскоростной)
        base_eff_ss = 0.75
        fm_factor = 1.0 - (fm_ratio - 0.3) * 0.25
        fm_factor = max(0.75, min(1.0, fm_factor))
        eff_ss = base_eff_ss * fm_factor
        eff_bod = eff_ss * 0.8 + 0.05
        
    elif method == 'membrane':
        # Мембранная ультрафильтрация
        eff_ss = 0.98
        eff_bod = 0.85
        fm_factor = 1.0 - (fm_ratio - 0.3) * 0.1
        eff_ss = eff_ss * max(0.95, min(1.0, fm_factor))
        eff_bod = eff_bod * max(0.95, min(1.0, fm_factor))
        
    elif method == 'carbon_filter':
        # Фильтр с активированным углём (сорбция)
        base_eff_bod = 0.80
        fm_factor = 1.0 - (fm_ratio - 0.3) * 0.4
        fm_factor = max(0.60, min(1.0, fm_factor))
        eff_bod = base_eff_bod * fm_factor
        eff_ss = 0.50
        
    elif method == 'coagulation_filtration':
        # Коагуляция + фильтрация
        base_eff_ss = 0.90
        base_eff_bod = 0.70
        fm_factor = 1.0 - (fm_ratio - 0.3) * 0.2
        fm_factor = max(0.80, min(1.0, fm_factor))
        eff_ss = base_eff_ss * fm_factor
        eff_bod = base_eff_bod * fm_factor
        
    elif method == 'none':
        return {
            'bod_out': bod_in,
            'ss_out': ss_in,
            'eff_bod': 0.0,
            'eff_ss': 0.0,
            'method': 'none'
        }
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Ограничиваем эффективность разумными пределами
    eff_ss = max(0.30, min(0.99, eff_ss))
    eff_bod = max(0.10, min(0.95, eff_bod))
    
    # Финальные концентрации
    ss_out = ss_in * (1 - eff_ss)
    bod_out = bod_in * (1 - eff_bod)
    
    return {
        'bod_in': bod_in,
        'bod_out': bod_out,
        'ss_in': ss_in,
        'ss_out': ss_out,
        'eff_bod': eff_bod * 100,
        'eff_ss': eff_ss * 100,
        'fm_ratio': fm_ratio,
        'ji': ji,
        'method': method
    }

