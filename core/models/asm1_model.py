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

# Отстойник
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

