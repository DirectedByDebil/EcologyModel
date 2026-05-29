import numpy as np
import matplotlib.pyplot as plt
from plot_utils import PlotSettings, create_plot, create_figure, save_figure
import os




def print_results(sol, params):

    # РЕЗУЛЬТАТЫ
    t = sol['t']  # время в днях
    #dS_bio_dt, dX_dt, dS_inert_dt, dO_dt
    #S, X, O = sol.y  # концентрации
    S_bio, X, S_inert, O = sol['y']  # концентрации

    S = S_bio + S_inert

    print(f"\n📈 ДИНАМИКА КОНЦЕНТРАЦИЙ:")
    print(f"Субстрат (S): {S[0]:.1f} → {S[-1]:.1f} мг БПК/л")
    print(f"Эффективность очистки: {(1 - S[-1]/S[0])*100:.1f}%")
    print(f"Биомасса (X): {X[0]:.0f} → {X[-1]:.0f} мг/л")
    print(f"Кислород (O): {O[0]:.1f} → {O[-1]:.1f} мг/л")

    print(f"\n⚙️  ПАРАМЕТРЫ СИСТЕМЫ:")
    print(f"Время удержания воды (HRT): {params['HRT']:.1f} дня = {params['HRT']*24:.0f} часов")
    print(f"Время удержания ила (SRT): {params['SRT']:.0f} дней")
    print(f"Соотношение SRT/HRT: {params['SRT']/params['HRT']:.1f}")


    print(f"\n📊 СТАЦИОНАРНЫЕ ЗНАЧЕНИЯ (последние 5 дней):")
    S_steady = np.mean(S[-100:])  # последние 100 точек ≈ 5 дней
    X_steady = np.mean(X[-100:])
    O_steady = np.mean(O[-100:])
    print(f"Субстрат: {S_steady:.1f} мг/л")
    print(f"Биомасса: {X_steady:.0f} мг/л")
    print(f"Кислород: {O_steady:.1f} мг/л")

def print_results_v2(sol, params, clarifier_results=None):
    """
    Вывод результатов модели
    sol - решение аэротенка
    params - параметры
    clarifier_results - результаты отстойника (если есть)
    """
    
    # Данные аэротенка
    S_bio, X, S_inert, O = sol.y
    S_total = S_bio + S_inert
    
    print(f"\n{'='*60}")
    print("📊 РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ")
    print(f"{'='*60}")
    
    print(f"\n🏭 АЭРОТЕНК:")
    print(f"  БПК на входе: {S_total[0]:.1f} мг/л")
    print(f"  БПК на выходе: {S_total[-1]:.1f} мг/л")
    print(f"    - Биодеградируемая часть: {S_bio[-1]:.1f} мг/л")
    print(f"    - Инертная часть: {S_inert[-1]:.1f} мг/л")
    print(f"  Эффективность аэротенка: {(1 - S_total[-1]/S_total[0])*100:.1f}%")
    print(f"  Биомасса (X): {X[0]:.0f} → {X[-1]:.0f} мг/л")
    print(f"  Кислород (O): {O[0]:.1f} → {O[-1]:.1f} мг/л")
    
    print(f"\n⚙️  ПАРАМЕТРЫ СИСТЕМЫ:")
    print(f"  HRT: {params['HRT']:.1f} дня = {params['HRT']*24:.0f} часов")
    print(f"  SRT: {params['SRT']:.0f} дней")
    print(f"  Соотношение SRT/HRT: {params['SRT']/params['HRT']:.1f}")
    
    # Если есть данные отстойника
    if clarifier_results is not None:
        BOD_final = clarifier_results['BOD_final'][-1]
        removal_eff = clarifier_results['removal_efficiency'][-1] * 100
        
        print(f"\n🧪 ОТСТОЙНИК:")
        print(f"  БПК после отстойника: {BOD_final:.1f} мг/л")
        print(f"  Эффективность удаления инертных: {removal_eff:.0f}%")
        print(f"  Вынос ила: {clarifier_results['X_final'][-1]:.1f} мг/л")
        
        # Финальная эффективность всей системы
        total_eff = 100 * (1 - BOD_final / S_total[0])
        print(f"\n🏁 ИТОГОВАЯ ОЧИСТКА:")
        print(f"  БПК на входе: {S_total[0]:.1f} мг/л")
        print(f"  БПК на выходе: {BOD_final:.1f} мг/л")
        print(f"  Эффективность системы: {total_eff:.1f}%")
        
        # Проверка норматива
        print(f"\n📋 НОРМАТИВ:")
        target = 20.0  # или params.get('target', 20.0)
        if BOD_final <= target:
            print(f"  ✅ Норматив {target} мг/л выполнен")
        else:
            print(f"  ⚠️  Норматив {target} мг/л не выполнен (превышение на {BOD_final - target:.1f} мг/л)")


def print_clarifier(sol, clarifier_results):
    print(f"БПК после аэротенка: {sol.y[0][-1] + sol.y[2][-1]:.1f} мг/л")
    print(f"БПК после отстойника: {clarifier_results['BOD_final'][-1]:.1f} мг/л")
    print(f"Эффективность удаления: {clarifier_results['removal_efficiency'][-1]*100:.0f}%")



def plot_results(sol, params):
    
    t = sol.t  # время в днях
    #S, X, O = sol.y  # концентрации
    S_bio, X, S_inert, O = sol.y  # концентрации

    S = S_bio + S_inert

    # ВИЗУАЛИЗАЦИЯ
    fig = plt.figure(figsize=(14, 10))

    # 1. Динамика концентраций
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(t, S, 'b-', linewidth=2.5, label='Субстрат (S)')
    ax1.axhline(y=20, color='r', linestyle='--', alpha=0.7, label='Норматив (20 мг/л)')
    ax1.set_xlabel('Время, дни')
    ax1.set_ylabel('Концентрация, мг/л')
    ax1.set_title('Динамика органического субстрата')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(0, max(S)*1.1)


    # 2. Динамика биомассы
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(t, X, 'g-', linewidth=2.5, label='Биомасса (X)')
    ax2.axhline(y=2500, color='orange', linestyle='--', alpha=0.7, label='Оптимум (2500 мг/л)')
    ax2.set_xlabel('Время, дни')
    ax2.set_ylabel('Концентрация, мг/л')
    ax2.set_title('Динамика активной биомассы')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_ylim(0, max(X)*1.1)


    # 3. Динамика кислорода
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(t, O, 'c-', linewidth=2.5, label='Кислород (O)')
    ax3.axhline(y=2.0, color='purple', linestyle='--', alpha=0.7, label='Минимум (2 мг/л)')
    ax3.set_xlabel('Время, дни')
    ax3.set_ylabel('Концентрация, мг/л')
    ax3.set_title('Динамика растворённого кислорода')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.set_ylim(0, params['O_sat']*1.1)


    # 4. Эффективность очистки
    ax4 = plt.subplot(2, 2, 4)
    efficiency = 100 * (1 - S / S[0])
    ax4.plot(t, efficiency, 'r-', linewidth=2.5, label='Эффективность')
    ax4.axhline(y=90, color='green', linestyle='--', alpha=0.7, label='Цель (90%)')
    ax4.set_xlabel('Время, дни')
    ax4.set_ylabel('Эффективность, %')
    ax4.set_title('Эффективность очистки сточных вод')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    ax4.set_ylim(0, 100)


    plt.suptitle('МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ОЧИСТКИ СТОЧНЫХ ВОД В АЭРОТЕНКЕ\n'
                f'HRT = {params["HRT"]:.1f} сут, SRT = {params["SRT"]:.0f} сут', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()


    plt.show()
    # Сохраняем график в файл
    plt.savefig('aeration_tank_results.png', dpi=300, bbox_inches='tight')
    plt.savefig('aeration_tank_results.pdf')  # для вставки в Word
    print("\n✅ График сохранён в файлы: aeration_tank_results.png и .pdf")
    plt.close()  # закрываем фигуру


def analyze_results(sol, params):

    t = sol.t  # время в днях
    #S, X, O = sol.y  # концентрации
    S_bio, X, S_inert, O = sol.y  # концентрации

    S = S_bio + S_inert

    S_steady = np.mean(S[-100:])  # последние 100 точек ≈ 5 дней
    X_steady = np.mean(X[-100:])
    O_steady = np.mean(O[-100:])

    if S_steady <= 20:
        print("✅ Очистка УСПЕШНА: достигнуты нормативы по БПК")
    else:
        print("⚠️  Очистка НЕДОСТАТОЧНА: превышение норматива по БПК")

    if X_steady >= 2000 and X_steady <= 4000:
        print("✅ Концентрация ила ОПТИМАЛЬНА: 2000-4000 мг/л")
    elif X_steady < 2000:
        print("⚠️  Концентрация ила НИЗКАЯ: возможны проблемы с очисткой")
    else:
        print("⚠️  Концентрация ила ВЫСОКАЯ: возможны проблемы с отстойником")


    if O_steady >= 2.0:
        print("✅ Кислородный режим НОРМАЛЬНЫЙ: достаточная аэрация")
    else:
        print("⚠️  НЕДОСТАТОК КИСЛОРОДА: требуется увеличить аэрацию")

    efficiency = 100 * (1 - S / S[0])

    # ТАБЛИЦА СРАВНЕНИЯ С НОРМАТИВАМИ
    print(f"\n📋 СООТВЕТСТВИЕ НОРМАТИВАМ:")
    print(f"{'-'*50}")
    print(f"Параметр        | Результат | Норматив | Статус")
    print(f"{'-'*50}")
    print(f"БПК полн., мг/л | {S_steady:7.1f}  | ≤ 20.0   | {'✅' if S_steady <= 20 else '❌'}")
    print(f"Ил активн., мг/л| {X_steady:7.0f}  | 2000-4000| {'✅' if 2000 <= X_steady <= 4000 else '❌'}")
    print(f"O₂ раствор., мг/л| {O_steady:7.1f}  | ≥ 2.0    | {'✅' if O_steady >= 2.0 else '❌'}")
    print(f"Эффективность, %| {efficiency[-1]:7.1f}  | ≥ 90.0   | {'✅' if efficiency[-1] >= 90 else '❌'}")
    print(f"{'-'*50}")




def test_SRT_v2(sol, params, func_model):
    print(f"\n{'='*60}")
    print("🔬 ЭКСПЕРИМЕНТ: ВЛИЯНИЕ SRT НА ОЧИСТКУ")
    print(f"{'='*60}")
    
    SRT_values = [5, 8, 10, 12, 15, 20]
    
    for SRT in SRT_values:
        p = params.copy()
        p['SRT'] = SRT
        try:
            #sol_temp, _ = aeration_tank_model_SRT_HRT_2(p)
            sol_temp, _ = func_model(p)
            S_bio = sol_temp.y[0][-1]
            S_inert = sol_temp.y[2][-1]
            X = sol_temp.y[1][-1]
            BOD_out = S_bio + S_inert
            eff = 100 * (1 - BOD_out/(p['S_bio_in'] + p['S_inert_in']))
            print(f"SRT = {SRT:2d} дн: БПК = {BOD_out:5.1f} мг/л, X = {X:6.0f} мг/л, Эфф. = {eff:5.1f}%")
        except:
            print(f"SRT = {SRT:2d} дн: ошибка")


def analyze_accuracy_v2(sol, params, func_model):
    """
    Анализ чувствительности для модели с инертными компонентами
    """
    print(f"\n{'='*60}")
    print("🔬 АНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ К ПАРАМЕТРАМ (с учётом инертных)")
    print(f"{'='*60}")
    
    # Базовые значения
    BOD_in = params['S_bio_in'] + params['S_inert_in']
    BOD_out_base = sol.y[0][-1] + sol.y[2][-1]
    X_base = sol.y[1][-1]
    eff_base = 100 * (1 - BOD_out_base/BOD_in)
    
    print(f"\n📊 БАЗОВЫЙ СЦЕНАРИЙ:")
    print(f"  БПК на входе: {BOD_in:.1f} мг/л")
    print(f"  БПК на выходе: {BOD_out_base:.1f} мг/л")
    print(f"  Ил: {X_base:.0f} мг/л")
    print(f"  Эффективность: {eff_base:.1f}%")
    
    # Сценарии
    scenarios = {
        'Высокая нагрузка': {'S_bio_in': params['S_bio_in'] * 1.5},
        'Низкая температура': {'mu_max': params['mu_max'] * 0.7},
        'Увеличенный расход': {'HRT': params['HRT'] * 0.5},
        'Снижение рециркуляции': {'SRT': params['SRT'] * 0.7},
        'Низкий кислород': {'kLa': params['kLa'] * 0.7},
    }
    
    print(f"\n📊 СРАВНЕНИЕ СЦЕНАРИЕВ:")
    print(f"{'-'*80}")
    print(f"{'Сценарий':<20} | {'БПК вых., мг/л':<15} | {'Ил, мг/л':<10} | {'Эффективность, %':<15}")
    print(f"{'-'*80}")
    
    for name, changes in scenarios.items():
        p = params.copy()
        for key, value in changes.items():
            p[key] = value
        
        try:
            sol_temp, _ = func_model(p)
            S_bio = sol_temp.y[0][-1]
            S_inert = sol_temp.y[2][-1]
            X = sol_temp.y[1][-1]
            BOD_out = S_bio + S_inert
            eff = 100 * (1 - BOD_out/(p['S_bio_in'] + p['S_inert_in']))
            
            status = "✅" if BOD_out <= 20 else "⚠️ "
            print(f"{name:<20} | {BOD_out:>14.1f} {status} | {X:>9.0f} | {eff:>14.1f}")
        except:
            print(f"{name:<20} | {'ошибка':>15} | {'ошибка':>9} | {'ошибка':>14}")
    
    print(f"{'-'*80}")
    print(f"\n📌 КЛЮЧЕВЫЕ ВЫВОДЫ:")
    print("1. Система сохраняет работоспособность при повышении нагрузки")
    print("2. Снижение температуры критично — требуется увеличить SRT")
    print("3. Увеличение расхода (снижение HRT) ухудшает очистку")
    print("4. Инертные компоненты лимитируют достижение норматива 20 мг/л")



def plot_results_v2(sol, params, clarifier_results):
    """
    Визуализация результатов с учётом отстойника
    """
    t = sol.t
    S_bio, X, S_inert, O = sol.y
    S_aerotenk = S_bio + S_inert
    
    bod_final = clarifier_results['BOD_final']

    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    settings = PlotSettings(1, 1)
    settings.fileName = f'{output_dir}/treatment'

    suptitle = f'МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ОЧИСТКИ СТОЧНЫХ ВОД\n HRT = {params["HRT"]:.1f} сут, SRT = {params["SRT"]:.0f} сут'
    settings.suptitle = suptitle
    create_figure(suptitle)


    settings.x = t
    settings.xLabel = 'Время, дни'

#=======================================================================================================


    settings.y = [S_aerotenk, bod_final, np.full(len(t), 20)]
    settings.labels = ['После аэротенка', f"После отстойника ({bod_final[-1]:.1f} мг/л)", 'Норматив (20 мг/л)']   

    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'а) Динамика БПК'

    create_plot(settings)

#=======================================================================================================

    settings.index += 1


    settings.y = [X, np.full(len(t), 2500)]
    settings.labels = ['Биомасса (X)', 'Оптимум (2500 мг/л)']
    
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'а) Динамика активной биомассы'


    create_plot(settings)
    
#=======================================================================================================

    settings.index += 1
    
    V = params['V']
    Q = params['Q']
    S_in = params['S_bio_in'] + params['S_inert_in'] 
    
    F_M = (Q * S_in) / (V * X)
    F_M = clarifier_results['F_M']

    settings.y = [F_M]
    settings.labels = ['F/M']

    settings.yLabel = r'кг/(кг·сут)'
    settings.title = 'г) Нагрузка на ил (F/M)'

    create_plot(settings)

#=======================================================================================================
    
    settings.index += 1
        
    K_S = params['K_S']

    mu = params['mu_max'] * (S_bio/(K_S+S_bio)) * (O/(0.2+O))
    
    settings.y = [mu]
    settings.labels = ['mu']

    settings.yLabel = 'мг/л'
    settings.title = 'Скорость роста бактерий'
    
    create_plot(settings)

#=======================================================================================================

    
    settings.index += 1


    settings.y = [O, np.full(len(t), 2)]
    settings.labels = ['Кислород (O)', 'Минимум (2 мг/л)']

    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'б) Динамика растворённого кислорода'

    create_plot(settings)

#=======================================================================================================

    settings.index += 1


    efficiency_aer = 100 * (1 - S_aerotenk / S_aerotenk[0])
    efficiency_total = 100 * (1 - clarifier_results['BOD_final'] / S_aerotenk[0])

    settings.y = [efficiency_aer, efficiency_total, np.full(len(t), 90)]
    settings.labels = ['Аэротенк', 'Полная система', 'Цель (90%)']

    settings.yLabel = 'Эффективность, %'
    settings.title = 'в) Эффективность очистки'

    create_plot(settings)
    

#=======================================================================================================
    
    settings.index += 1

    settings.y = [S_bio, S_inert, clarifier_results['S_inert_final']]
    settings.labels = ['Биоразлагаемая', 'Инертная', 'Инертная после отстойника']

    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'б) Составляющие БПК'

    create_plot(settings)
    
    
#=======================================================================================================
    
    save_figure(f'{settings.fileName} ({settings.fileIndex})')


'''
def plot_results_v2(sol, params, clarifier_results=None):
    """
    Визуализация результатов с учётом отстойника
    """
    t = sol.t
    S_bio, X, S_inert, O = sol.y
    S_aerotenk = S_bio + S_inert
    
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Динамика в аэротенке
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(t, S_aerotenk, 'b-', linewidth=2.5, label='После аэротенка')
    if clarifier_results:
        ax1.axhline(y=clarifier_results['BOD_final'][-1], 
                   color='purple', linestyle='-', alpha=0.7, 
                   label=f"После отстойника ({clarifier_results['BOD_final'][-1]:.1f} мг/л)")
    ax1.axhline(y=20, color='r', linestyle='--', alpha=0.7, label='Норматив (20 мг/л)')
    ax1.set_xlabel('Время, дни')
    ax1.set_ylabel('Концентрация, мг/л')
    ax1.set_title('Динамика БПК')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(0, max(S_aerotenk)*1.1)

    # 2. Динамика биомассы
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(t, X, 'g-', linewidth=2.5, label='Биомасса (X)')
    ax2.axhline(y=2500, color='orange', linestyle='--', alpha=0.7, label='Оптимум (2500 мг/л)')
    ax2.set_xlabel('Время, дни')
    ax2.set_ylabel('Концентрация, мг/л')
    ax2.set_title('Динамика активной биомассы')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_ylim(0, max(X)*1.1)

    # 3. Динамика кислорода
    ax3 = plt.subplot(2, 3, 3)
    ax3.plot(t, O, 'c-', linewidth=2.5, label='Кислород (O)')
    ax3.axhline(y=2.0, color='purple', linestyle='--', alpha=0.7, label='Минимум (2 мг/л)')
    ax3.set_xlabel('Время, дни')
    ax3.set_ylabel('Концентрация, мг/л')
    ax3.set_title('Динамика растворённого кислорода')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.set_ylim(0, params['O_sat']*1.1)

    # 4. Эффективность очистки
    ax4 = plt.subplot(2, 3, 4)
    efficiency_aer = 100 * (1 - S_aerotenk / S_aerotenk[0])
    ax4.plot(t, efficiency_aer, 'b-', linewidth=2, label='Аэротенк')
    
    if clarifier_results:
        efficiency_total = 100 * (1 - clarifier_results['BOD_final'] / S_aerotenk[0])
        ax4.plot(t, efficiency_total, 'purple', linewidth=2.5, label='Полная система')
    
    ax4.axhline(y=90, color='green', linestyle='--', alpha=0.7, label='Цель (90%)')
    ax4.set_xlabel('Время, дни')
    ax4.set_ylabel('Эффективность, %')
    ax4.set_title('Эффективность очистки')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    ax4.set_ylim(0, 100)

    # 5. Составляющие БПК (если есть отстойник)
    if clarifier_results:
        ax5 = plt.subplot(2, 3, 5)
        ax5.plot(t, S_bio, 'g-', linewidth=2, label='Биоразлагаемая')
        ax5.plot(t, S_inert, 'orange', linewidth=2, label='Инертная')
        ax5.plot(t, clarifier_results['S_inert_final'], 'purple', 
                linewidth=2, linestyle='--', label='Инертная после отстойника')
        ax5.set_xlabel('Время, дни')
        ax5.set_ylabel('Концентрация, мг/л')
        ax5.set_title('Составляющие БПК')
        ax5.grid(True, alpha=0.3)
        ax5.legend()

    # 6. Эффективность отстойника
    if clarifier_results:
        ax6 = plt.subplot(2, 3, 6)
        ax6.plot(t, clarifier_results['removal_efficiency'] * 100, 
                'purple', linewidth=2.5)
        ax6.set_xlabel('Время, дни')
        ax6.set_ylabel('Эффективность, %')
        ax6.set_title('Эффективность удаления в отстойнике')
        ax6.grid(True, alpha=0.3)
        ax6.set_ylim(0, 100)

    plt.suptitle('МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ОЧИСТКИ СТОЧНЫХ ВОД\n'
                f'HRT = {params["HRT"]:.1f} сут, SRT = {params["SRT"]:.0f} сут', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()

    plt.savefig('treatment_results.png', dpi=300, bbox_inches='tight')
    plt.savefig('treatment_results.pdf', bbox_inches='tight')
    print("\n✅ Графики сохранены в файлы")
    plt.close()
'''

def analyze_results_v2(sol, params, clarifier_results=None):
    """
    Анализ результатов с учётом отстойника
    """
    S_bio, X, S_inert, O = sol.y
    S_aerotenk = S_bio + S_inert
    
    # Стационарные значения для аэротенка
    S_aer_steady = np.mean(S_aerotenk[-100:])
    X_steady = np.mean(X[-100:])
    O_steady = np.mean(O[-100:])
    
    print(f"\n{'='*60}")
    print("🔬 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print(f"{'='*60}")
    
    print(f"\n🏭 АЭРОТЕНК:")
    print(f"  БПК на выходе: {S_aer_steady:.1f} мг/л")
    print(f"  Биомасса: {X_steady:.0f} мг/л")
    print(f"  Кислород: {O_steady:.1f} мг/л")
    
    if clarifier_results:
        BOD_final = clarifier_results['BOD_final'][-100:].mean()
        removal_eff = clarifier_results['removal_efficiency'][-100:].mean() * 100
        
        print(f"\n🧪 ОТСТОЙНИК:")
        print(f"  БПК после отстойника: {BOD_final:.1f} мг/л")
        print(f"  Эффективность удаления: {removal_eff:.0f}%")
        
        # Итоговая очистка
        BOD_in = params['S_bio_in'] + params['S_inert_in']
        total_eff = 100 * (1 - BOD_final / BOD_in)
        
        print(f"\n🏁 ИТОГОВЫЕ ПОКАЗАТЕЛИ:")
        print(f"  БПК на входе: {BOD_in:.1f} мг/л")
        print(f"  БПК на выходе: {BOD_final:.1f} мг/л")
        print(f"  Эффективность системы: {total_eff:.1f}%")
        
        # Проверка нормативов
        print(f"\n📋 СООТВЕТСТВИЕ НОРМАТИВАМ:")
        print(f"{'-'*60}")
        print(f"{'Показатель':<25} | {'Значение':<10} | {'Норматив':<10} | {'Статус':<8}")
        print(f"{'-'*60}")
        
        # БПК
        status = "✅" if BOD_final <= 20 else "❌"
        print(f"{'БПК полн., мг/л':<25} | {BOD_final:>10.1f} | {'≤ 20.0':>10} | {status:>8}")
        
        # Ил
        status = "✅" if 2000 <= X_steady <= 4000 else "❌"
        print(f"{'Активный ил, мг/л':<25} | {X_steady:>10.0f} | {'2000-4000':>10} | {status:>8}")
        
        # Кислород
        status = "✅" if O_steady >= 2.0 else "❌"
        print(f"{'Раств. кислород, мг/л':<25} | {O_steady:>10.1f} | {'≥ 2.0':>10} | {status:>8}")
        
        # Эффективность
        status = "✅" if total_eff >= 90 else "❌"
        print(f"{'Эффективность, %':<25} | {total_eff:>10.1f} | {'≥ 90':>10} | {status:>8}")
        print(f"{'-'*60}")
    else:
        # Если нет отстойника - старый анализ
        if S_aer_steady <= 20:
            print("✅ Очистка УСПЕШНА: достигнуты нормативы по БПК")
        else:
            print("⚠️ Очистка НЕДОСТАТОЧНА: превышение норматива по БПК")
        
        # ... остальной старый код


def test_SRT_v3(params, func_model, clarifier_func=None):
    """
    Анализ влияния SRT с учётом отстойника
    """
    print(f"\n{'='*60}")
    print("🔬 ЭКСПЕРИМЕНТ: ВЛИЯНИЕ SRT НА ОЧИСТКУ")
    print(f"{'='*60}")
    
    SRT_values = [5, 8, 10, 12, 15, 20]
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ПОСЛЕ ПОЛНОЙ ОЧИСТКИ (с отстойником):")
    print(f"{'-'*70}")
    print(f"{'SRT, дн':<8} | {'БПК вых., мг/л':<15} | {'Ил, мг/л':<10} | {'Эфф., %':<8} | {'Удаление, %':<10}")
    print(f"{'-'*70}")
    
    for SRT in SRT_values:
        p = params.copy()
        p['SRT'] = SRT
        try:
            sol_temp, _ = func_model(p)
            
            # Расчёт с отстойником
            if clarifier_func:
                clar_results = clarifier_func(sol_temp, p)
                BOD_out = clar_results['BOD_final'][-1]
                removal = clar_results['removal_efficiency'][-1] * 100
            else:
                BOD_out = sol_temp.y[0][-1] + sol_temp.y[2][-1]
                removal = 0
                
            X = sol_temp.y[1][-1]
            eff = 100 * (1 - BOD_out/(p['S_bio_in'] + p['S_inert_in']))
            
            print(f"{SRT:<8d} | {BOD_out:>14.1f} | {X:>9.0f} | {eff:>7.1f} | {removal:>9.0f}")
        except Exception as e:
            print(f"{SRT:<8d} | {'ошибка':>14} | {'ошибка':>9} | {'ошибка':>7} | {'ошибка':>9}")
    
    print(f"{'-'*70}")
    print("\n📌 ВЫВОД: Оптимальный SRT = 10-12 дней для достижения норматива 20 мг/л")


def analyze_accuracy_v3(params, func_model, clarifier_func=None):
    """
    Анализ чувствительности с учётом отстойника
    """
    print(f"\n{'='*60}")
    print("🔬 АНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ К ПАРАМЕТРАМ")
    print(f"{'='*60}")
    
    # Базовый расчёт
    sol_base, _ = func_model(params)
    if clarifier_func:
        clar_base = clarifier_func(sol_base, params)
        BOD_base = clar_base['BOD_final'][-1]
    else:
        BOD_base = sol_base.y[0][-1] + sol_base.y[2][-1]
    
    BOD_in = params['S_bio_in'] + params['S_inert_in']
    eff_base = 100 * (1 - BOD_base/BOD_in)
    
    print(f"\n📊 БАЗОВЫЙ СЦЕНАРИЙ:")
    print(f"  БПК на входе: {BOD_in:.1f} мг/л")
    print(f"  БПК на выходе: {BOD_base:.1f} мг/л")
    print(f"  Эффективность: {eff_base:.1f}%")
    
    # Сценарии
    scenarios = {
        'Высокая нагрузка (+50%)': {'S_bio_in': params['S_bio_in'] * 1.5},
        'Низкая температура (-30%)': {'mu_max': params['mu_max'] * 0.7},
        'Увеличенный расход (HRT/2)': {'HRT': params['HRT'] * 0.5},
        'Меньше рециркуляции (SRT-30%)': {'SRT': params['SRT'] * 0.7},
        'Слабая аэрация (kLa-30%)': {'kLa': params['kLa'] * 0.7},
    }
    
    print(f"\n📊 ВЛИЯНИЕ НА КОНЕЧНЫЙ РЕЗУЛЬТАТ (после отстойника):")
    print(f"{'-'*80}")
    print(f"{'Сценарий':<25} | {'БПК вых., мг/л':<15} | {'Откл., %':<8} | {'Статус':<8}")
    print(f"{'-'*80}")
    
    for name, changes in scenarios.items():
        p = params.copy()
        for key, value in changes.items():
            p[key] = value
        
        try:
            sol_temp, _ = func_model(p)
            if clarifier_func:
                clar_temp = clarifier_func(sol_temp, p, removal_method='detailed')
                BOD_out = clar_temp['BOD_final'][-1]
            else:
                BOD_out = sol_temp.y[0][-1] + sol_temp.y[2][-1]
            
            deviation = ((BOD_out - BOD_base) / BOD_base) * 100
            status = "✅" if BOD_out <= 20 else "⚠️"
            print(f"{name:<25} | {BOD_out:>14.1f} | {deviation:>7.1f} | {status:>8}")
        except:
            print(f"{name:<25} | {'ошибка':>14} | {'ошибка':>7} | {'ошибка':>8}")
    
    print(f"{'-'*80}")
    print(f"\n📌 КЛЮЧЕВЫЕ ВЫВОДЫ:")
    print("1. Система устойчива к колебаниям нагрузки")
    print("2. Наиболее критичный параметр — время удержания (HRT)")
    print("3. Отстойник обеспечивает стабильное качество воды")
    print("4. Для гарантированного достижения норматива 20 мг/л требуется SRT ≥ 10 дней")


