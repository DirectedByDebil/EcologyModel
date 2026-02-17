import numpy as np
from scipy.integrate import solve_ivp
import asm1_view as av

def aeration_tank_model_SRT_HRT_2(params: object = None):
    """
    Реалистичная модель аэротенка очистки сточных вод
    с разделением времени удержания воды (HRT) и ила (SRT)
    и учётом инертных компонентов БПК
    """
    
    if params is None:
        print("Используются параметры по умолчанию (на основе данных Водоканала)")
        
        # ПАРАМЕТРЫ МОДЕЛИ (на основе реальных данных)
        params = {
            # Кинетические параметры
            'Y': 0.67,           # Урожайность, г биомассы / г субстрата
            'mu_max': 7.5,       # Максимальная скорость роста, 1/день
            'K_S': 25.0,         # Константа полунасыщения, мг/л
            'b': 0.12,           # Скорость эндогенного дыхания, 1/день
            
            # Гидравлические параметры
            'HRT': 0.5,          # 12 часов
            'SRT': 10.0,         # 10 дней
            
            # Концентрации на входе (по данным Водоканала)
            'S_bio_in': 150.0,   # Биодеградируемый субстрат, мг/л (82% от БПК)
            'S_inert_in': 32.5,  # Инертный субстрат, мг/л (18% от БПК) - НЕ ОЧИЩАЕТСЯ!
            'X_in': 3000.0,      # Биомасса на входе, мг/л
            'O_in': 1.5,         # Кислород на входе, мг/л
            
            # Параметры аэрации
            'kLa': 35.0,         # Умеренная аэрация
            'O_sat': 8.0,        # Насыщение кислородом, мг/л
        }

    # СИСТЕМА ДИФФЕРЕНЦИАЛЬНЫХ УРАВНЕНИЙ
    def system_odes(t, y, params):
        """
        y = [S_bio, X, S_inert, O]
        S_bio - биодеградируемый субстрат (очищается)
        X - активная биомасса
        S_inert - инертный субстрат (НЕ очищается биологически)
        O - растворённый кислород
        """
        S_bio, X, S_inert, O = y
        
        # Скорость роста с двойным лимитированием
        mu = params['mu_max'] * (S_bio / (params['K_S'] + S_bio)) * (O / (0.2 + O))
        
        #'X_max' = 5000
        # И в уравнениях:
        #mu = mu_max * (S/(K_S+S)) * (O/(0.2+O)) * (1 - X/X_max)
        
        # 1. Биодеградируемый субстрат - потребляется бактериями
        dS_bio_dt = (params['S_bio_in'] - S_bio) / params['HRT'] \
                    - (mu / params['Y']) * X
        
        # 2. Биомасса - растёт и отмирает
        dX_dt = (params['X_in'] - X) / params['SRT'] \
                + mu * X - params['b'] * X
        
        # 3. Инертный субстрат - ТОЛЬКО РАЗБАВЛЕНИЕ, не потребляется!
        dS_inert_dt = (params['S_inert_in'] - S_inert) / params['HRT']
        
        # 4. Кислород - аэрация + потребление
        dO_dt = (params['O_in'] - O) / params['HRT'] \
                + params['kLa'] * (params['O_sat'] - O) \
                - ((1 - params['Y']) / params['Y']) * mu * X
        
        return [dS_bio_dt, dX_dt, dS_inert_dt, dO_dt]
    
    def system_odes_2(t, y, params):
        S_bio, X, S_inert, O = y
        
        # Скорость роста с ТРЕМЯ лимитами:
        # 1. Лимит по субстрату (Моно)
        # 2. Лимит по кислороду
        # 3. Лимит по плотности (новый!)
        
        # Лимит по субстрату и кислороду
        mu_monod = params['mu_max'] * (S_bio / (params['K_S'] + S_bio)) * (O / (0.2 + O))
        
        # Лимит по плотности (логистическое торможение)
        # Чем ближе X к X_max, тем медленнее рост
        density_limit = max(0, 1 - X / params['X_max'])
        
        # Итоговая скорость роста
        mu = mu_monod * density_limit

        # Остальные уравнения без изменений
        dS_bio_dt = (params['S_bio_in'] - S_bio) / params['HRT'] - (mu / params['Y']) * X
        dX_dt = (params['X_in'] - X) / params['SRT'] + mu * X - params['b'] * X
        dS_inert_dt = (params['S_inert_in'] - S_inert) / params['HRT']
        dO_dt = (params['O_in'] - O) / params['HRT'] + params['kLa'] * (params['O_sat'] - O) - ((1 - params['Y']) / params['Y']) * mu * X
        
        return [dS_bio_dt, dX_dt, dS_inert_dt, dO_dt]


    # НАЧАЛЬНЫЕ УСЛОВИЯ
    y0 = [
        params['S_bio_in'],      # S_bio0 - биодеградируемый
        params['X_in'],          # X0 - биомасса
        params['S_inert_in'],    # S_inert0 - инертный
        params['O_in']           # O0 - кислород
    ]
    
    # ВРЕМЯ МОДЕЛИРОВАНИЯ
    t_span = (0, 30)  # 30 дней
    t_eval = np.linspace(0, 30, 1000)
    
    # РЕШЕНИЕ СИСТЕМЫ ОДУ
    sol = solve_ivp(
        system_odes_2,
        t_span,
        y0,
        args=(params,),
        t_eval=t_eval,
        method='BDF',
        rtol=1e-6,
        atol=1e-8
    )
    
    return sol, params


def secondary_clarifier(sol, params, removal_method='standard'):
    """
    Модель вторичного отстойника
    
    Parameters:
    -----------
    sol : решение solve_ivp
    params : параметры модели
    removal_method : 'simple', 'standard', или 'detailed'
    """
    
    # Извлекаем данные из решения
    t = sol.t
    S_bio = sol.y[0]      # биодеградируемый субстрат
    X = sol.y[1]          # биомасса
    S_inert = sol.y[2]    # инертный субстрат
    O = sol.y[3]          # кислород
    
    # Доза ила в аэротенке (г/л)
    MLSS = X / 1000
    
    # Иловая нагрузка (кг БПК/кг ила·сут)
    F_M = (params['S_bio_in'] * 24/params['HRT']) / MLSS / 1000
    
    if removal_method == 'simple':
        # Простое удаление 50%
        removal_efficiency = 0.5 * np.ones_like(t)
        
    elif removal_method == 'standard':
        # Эффективность зависит от нагрузки ила
        removal_efficiency = np.clip(0.3 + 0.1 * F_M, 0.3, 0.7)
        
    elif removal_method == 'detailed':
        # Модель Эмшера
        H = 3.0  # глубина отстойника, м
        v = 1.2  # скорость восходящего потока, м/ч
        k = 0.15  # эмпирический коэффициент
        removal_efficiency = 1 - np.exp(-k * H / v)
        removal_efficiency = removal_efficiency * np.ones_like(t)

        #removal_efficiency = 0.5 * (1 - np.exp(-k * H / v))  # ещё и множитель 0.5
        #removal_efficiency = np.clip(removal_efficiency, 0.4, 0.6) * np.ones_like(t)
    
    # Удаление инертных веществ
    S_inert_final = S_inert * (1 - removal_efficiency)
    
    # Итоговый БПК после полной очистки
    BOD_final = S_bio + S_inert_final
    
    # Удаление биомассы (вынос ила)
    X_final = X * 0.01  # 1% вынос
    
    return {
        't': t,
        'S_bio': S_bio,
        'X': X,
        'S_inert': S_inert,
        'S_inert_final': S_inert_final,
        'BOD_final': BOD_final,
        'X_final': X_final,
        'removal_efficiency': removal_efficiency,
        'MLSS': MLSS,
        'F_M': F_M
    }



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
    F_M = (params['S_bio_in'] * params['Q'] / params['V']) / MLSS / 1000  # нагрузка на ил
    
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


# Анализ результатов
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


'''
    # Аэрация
    'kLa': 100/24,       # коэф. массопередачи кислорода, 1/ч
    'O_sat': 8.0,        # насыщение кислородом, мг/л
    
    # Входные концентрации (по факту)
    'S_bio_in': 150.0,   # биодеградируемый субстрат, мг/л
    'S_inert_in': 32.5,  # инертный субстрат, мг/л
    'X_in': 100.0,       # биомасса на входе, мг/л
    'O_in': 2.0,         # кислород на входе, мг/л
'''



# Данные Волжского
params_vlj = {
    # Кинетические параметры (ASM1 стандартные)
    'Y': 0.67,           # Урожайность, г биомассы / г субстрата
    'K_S': 120.0,         # Константа полунасыщения, мг/л


    # Концентрации на входе (по данным Водоканала)
    'mu_max': 3.5,       # Было 8.0 - чуть медленнее рост
    'b': 0.15,           # Было 0.1 - чуть больше отмирание
    
    'V': 5000,           # объём аэротенка, м³
    'Q': 1000,           # расход, м³/ч
    # Тогда HRT = V/Q = 5 ч, а не 0.5 дня

    # Гидравлические параметры
    'HRT': 1,          # Время удержания воды: 0.5 дня = 12 часов
    'SRT': 10.0,         # Время удержания ила: 10 дней

    # Концентрации на входе
    'S_in': 182.5,       # Входная концентрация субстрата, мг БПК/л
    'S_bio_in': 150.0,   # Биодеградируемый субстрат, мг/л (82% от БПК)
    'S_inert_in': 32.5,  # Инертный субстрат, мг/л (18% от БПК) - НЕ ОЧИЩАЕТСЯ!
    'X_in': 3000.0,       # Входная концентрация биомассы, мг/л
    'O_in': 1.5,         # Кислород на входе, мг/л

    # Параметры аэрации
    'kLa': 25.0,        # Коэффициент массопередачи кислорода, 1/день
    'O_sat': 8.0,        # Насыщенная концентрация к
    
    # Рециркуляция
    'r': 0.57,            # коэффициент рециркуляции (50%)
    'X_r_max': 8000,     # макс. концентрация ила в рецикле, мг/л
    'eta': 0.3,          # удаление инертных в отстойнике (30%)

    'K_O': 0.5,          # константа по кислороду, мг/л
    #'b': 0.1/24,         # скорость эндогенного дыхания, 1/ч
    'X_max': 8000,       # максимальная концентрация ила, мг/л
    'tau_adapt': 36,     # время адаптации бактерий, ч (1.5 дня)
}


# Данные другие
params_2 = {
    # Кинетика
    'Y': 0.67,
    'mu_max': 7.5,
    'K_S': 25.0,
    'b': 0.12,
    
    # Гидравлика
    'HRT': 0.5,
    'SRT': 12.0,           # Увеличил для нитрификации
    
    # Вход (по данным таблицы 3)
    'S_bio_in': 125.0,     # 80% от БПК = 156.1 * 0.8
    'S_inert_in': 31.1,    # 20% от БПК
    'NH_in': 30.2,         # Аммоний
    'X_in': 3000.0,
    'O_in': 1.5,
    
    # Параметры аэрации
    'kLa': 40.0,
    'O_sat': 8.0,
}





# Запуск
sol, params = aeration_tank_physical(params_vlj)
params['S_in'] = params['S_bio_in'] + params['S_inert_in']

clar = secondary_clarifier_physical(sol, params)
analyze_physical(sol, params, clar)

av.plot_results_v2(sol, params, clar)

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


S_bio, X, S_inert, O = sol.y
S_aerotenk = S_bio + S_inert

bod_final = clar['BOD_final']

file_path = "S_aerotenk.txt"
np.savetxt(file_path, S_aerotenk)






'''
print("🚀 Запуск реалистичной модели аэротенка...")

sol, params = aeration_tank_model_SRT_HRT_2(params_vlj)
params['S_in'] = params['S_bio_in'] + params['S_inert_in']


clarifier_results = secondary_clarifier(sol, params)
#av.print_clarifier(sol, clarifier_results)


S_bio, X, S_inert, O = sol.y
S_aerotenk = S_bio + S_inert

bod_final = clarifier_results['BOD_final']

file_path = "results.txt"
np.savetxt(file_path, S_aerotenk)



#av.print_results_v2(sol, params, clarifier_results)
av.plot_results_v2(sol, params, clarifier_results)
'''

#av.analyze_results_v2(sol, params, clarifier_results)

#av.test_SRT_v3(params, aeration_tank_model_SRT_HRT_2, secondary_clarifier)
#av.analyze_accuracy_v3(params, aeration_tank_model_SRT_HRT_2, secondary_clarifier)







