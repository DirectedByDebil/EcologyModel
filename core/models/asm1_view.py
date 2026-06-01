import numpy as np
import matplotlib.pyplot as plt
from plot_utils import PlotSettings, create_plot, create_figure, save_figure
import os


def plot_simple(sol, params, clarifier_results, tertiary_treatment):
    t = sol.t
    S_bio, X, S_inert, O = sol.y
    S_aerotenk = S_bio + S_inert
    
    bod_final = clarifier_results['BOD_final']

    output_dir = "results/simple"
    os.makedirs(output_dir, exist_ok=True)

    settings = PlotSettings(1, 1)
    settings.fileName = f'{output_dir}/treatment_simple'

    suptitle = f'МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ОЧИСТКИ СТОЧНЫХ ВОД\n HRT = {params["HRT"]:.1f} сут, SRT = {params["SRT"]:.0f} сут'
    settings.suptitle = suptitle
    create_figure(suptitle)

    settings.x = t
    settings.xLabel = 'Время, дни'

    # ============= 1. Динамика БПК =============
    # Базовые линии
    settings.y = [S_aerotenk, bod_final, np.full(len(t), 20)]
    settings.labels = ['После аэротенка', f"После отстойника ({bod_final[-1]:.1f} мг/л)", 'Норматив (20 мг/л)']
    
    # Добавляем линии  для каждого метода
    if tertiary_treatment:
        for tt in tertiary_treatment:
            bod_tertiary = tt['data']['bod_out']
            method = tt['method']
            settings.y.append(np.full(len(t), bod_tertiary))
            settings.labels.append(f" ({method}) ({bod_tertiary:.1f} мг/л)")
    
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'а) Динамика БПК'
    create_plot(settings)
    settings.index += 1

    # ============= 2. Динамика активной биомассы =============
    settings.y = [X, np.full(len(t), 2500)]
    settings.labels = ['Биомасса (X)', 'Оптимум (2500 мг/л)']
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'а) Динамика активной биомассы'
    create_plot(settings)
    settings.index += 1

    # ============= 3. Нагрузка на ил (F/M) =============
    V = params['V']
    Q = params['Q']
    S_in = params['S_bio_in'] + params['S_inert_in'] 
    
    F_M_plot = clarifier_results['F_M']
    settings.y = [F_M_plot]
    settings.labels = ['F/M']
    settings.yLabel = r'кг/(кг·сут)'
    settings.title = 'г) Нагрузка на ил (F/M)'
    create_plot(settings)
    settings.index += 1

    # ============= 4. Скорость роста бактерий =============
    K_S = params['K_S']
    mu = params['mu_max'] * (S_bio/(K_S+S_bio)) * (O/(0.2+O))
    settings.y = [mu]
    settings.labels = ['mu']
    settings.yLabel = '1/день'
    settings.title = 'Скорость роста бактерий'
    create_plot(settings)
    settings.index += 1

    # ============= 5. Динамика растворённого кислорода =============
    settings.y = [O, np.full(len(t), 2)]
    settings.labels = ['Кислород (O)', 'Минимум (2 мг/л)']
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'б) Динамика растворённого кислорода'
    create_plot(settings)
    settings.index += 1

    # ============= 6. Эффективность очистки =============
    efficiency_aer = 100 * (1 - S_aerotenk / S_aerotenk[0])
    efficiency_total = 100 * (1 - clarifier_results['BOD_final'] / S_aerotenk[0])
    
    settings.y = [efficiency_aer, efficiency_total, np.full(len(t), 90)]
    settings.labels = [
        f"Аэротенк ({efficiency_aer[-1]:.1f}%)",
        f"Полная система ({efficiency_total[-1]:.1f}%)",
        'Цель (90%)'
    ]
    
    # Добавляем эффективность 
    if tertiary_treatment:
        for tt in tertiary_treatment:
            bod_tertiary = tt['data']['bod_out']
            method = tt['method']
            efficiency_tertiary = 100 * (1 - bod_tertiary / S_aerotenk[0])
            settings.y.append(np.full(len(t), efficiency_tertiary))
            settings.labels.append(f"С доочисткой ({method}) ({efficiency_tertiary:.1f}%)")
    
    settings.yLabel = 'Эффективность, %'
    settings.title = 'в) Эффективность очистки'
    create_plot(settings)
    settings.index += 1

    # ============= 7. Составляющие БПК =============
    settings.y = [S_bio, S_inert, clarifier_results['S_inert_final']]
    settings.labels = ['Биоразлагаемая', 'Инертная', 'Инертная после отстойника']
    
    # Добавляем инертные  (если есть в данных)
    if tertiary_treatment:
        for tt in tertiary_treatment:
            if 'ss_out' in tt['data']:
                s_inert_tertiary = tt['data']['ss_out']
                method = tt['method']
                settings.y.append(np.full(len(t), s_inert_tertiary))
                settings.labels.append(f"Инертная  ({method})")
    
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'б) Составляющие БПК'
    create_plot(settings)
    
    save_figure(f'{settings.fileName} ({settings.fileIndex})')


def plot_with_nitri(sol, params, clarifier_results, tertiary_treatment):
    """
    Визуализация результатов для модели с нитрификацией и денитрификацией
    """
    t = sol.t
    S_bio, X_BH, S_inert, X_BA, S_NH, S_NO, O = sol.y
    S_aerotenk = S_bio + S_inert
    X_total = X_BH + X_BA
    
    bod_final = clarifier_results['BOD_final']
    s_inert_final = clarifier_results['S_inert_final']

    output_dir = "results/with_nitri"
    os.makedirs(output_dir, exist_ok=True)

    settings = PlotSettings(1, 1)
    settings.fileName = f'{output_dir}/treatment_nitri'

    suptitle = f'МОДЕЛЬ С НИТРИФИКАЦИЕЙ И ДЕНИТРИФИКАЦИЕЙ\nHRT = {params["HRT"]:.1f} сут, SRT = {params["SRT"]:.0f} сут'
    settings.suptitle = suptitle
    create_figure(suptitle)

    settings.x = t
    settings.xLabel = 'Время, дни'

    # ============= 1. Динамика БПК =============
    settings.y = [S_aerotenk, bod_final, np.full(len(t), 20)]
    settings.labels = ['После аэротенка', f"После отстойника ({bod_final[-1]:.1f} мг/л)", 'Норматив (20 мг/л)']
    
    if tertiary_treatment:
        for tt in tertiary_treatment:
            bod_tertiary = tt['data']['bod_out']
            method = tt['method']
            settings.y.append(np.full(len(t), bod_tertiary))
            settings.labels.append(f" ({method}) ({bod_tertiary:.1f} мг/л)")
    
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'а) Динамика БПК'
    create_plot(settings)
    settings.index += 1

    # ============= 2. Составляющие БПК =============
    settings.y = [S_bio, S_inert, s_inert_final]
    settings.labels = ['Биоразлагаемая', 'Инертная', 'Инертная после отстойника']
    
    if tertiary_treatment:
        for tt in tertiary_treatment:
            if 'ss_out' in tt['data']:
                s_inert_tertiary = tt['data']['ss_out']
                method = tt['method']
                settings.y.append(np.full(len(t), s_inert_tertiary))
                settings.labels.append(f"Инертная  ({method})")
    
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'б) Составляющие БПК'
    create_plot(settings)
    settings.index += 1

    # ============= 3. Эффективность очистки =============
    efficiency_aer = 100 * (1 - S_aerotenk / S_aerotenk[0])
    efficiency_total = 100 * (1 - bod_final / S_aerotenk[0])
    
    settings.y = [efficiency_aer, efficiency_total, np.full(len(t), 90)]
    settings.labels = [
        f"Аэротенк ({efficiency_aer[-1]:.1f}%)",
        f"Полная система ({efficiency_total[-1]:.1f}%)",
        'Цель (90%)'
    ]
    
    if tertiary_treatment:
        for tt in tertiary_treatment:
            bod_tertiary = tt['data']['bod_out']
            method = tt['method']
            efficiency_tertiary = 100 * (1 - bod_tertiary / S_aerotenk[0])
            settings.y.append(np.full(len(t), efficiency_tertiary))
            settings.labels.append(f"С доочисткой ({method}) ({efficiency_tertiary:.1f}%)")
    
    settings.yLabel = 'Эффективность, %'
    settings.title = 'в) Эффективность очистки'
    create_plot(settings)
    settings.index += 1

    # ============= 4. Нагрузка на ил (F/M) =============
    V = params['V']
    Q = params['Q']
    S_in = params['S_bio_in'] + params['S_inert_in']
    if 'F_M' in clarifier_results:
        F_M_plot = clarifier_results['F_M']
    else:
        MLSS = X_total / 1000
        F_M_calc = (Q * 24 * S_in) / (V * MLSS) / 1000
        F_M_plot = F_M_calc * np.ones_like(t)
    
    settings.y = [F_M_plot]
    settings.labels = ['F/M']
    settings.yLabel = r'кг/(кг·сут)'
    settings.title = 'г) Нагрузка на ил (F/M)'
    create_plot(settings)
    settings.index += 1

    # ============= 5. Биомасса =============
    settings.y = [X_BH, X_BA, X_total, np.full(len(t), 2500)]
    settings.labels = ['Гетеротрофы (X_BH)', 'Автотрофы (X_BA)', 'Общая биомасса', 'Оптимум (2500 мг/л)']
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'д) Динамика активной биомассы'
    create_plot(settings)
    settings.index += 1

    # ============= 6. Кислород =============
    settings.y = [O, np.full(len(t), 2)]
    settings.labels = ['Кислород (O)', 'Минимум (2 мг/л)']
    settings.yLabel = 'Концентрация, мг/л'
    settings.title = 'е) Динамика растворённого кислорода'
    create_plot(settings)
    settings.index += 1

    # ============= 7. Азот =============
    if settings.index > settings.rows * settings.cols:
        save_figure(f'{settings.fileName} ({settings.fileIndex})')
        create_figure(suptitle)
        settings.index = 1
        settings.fileIndex += 1

    settings.y = [S_NH, S_NO]
    settings.labels = ['Аммоний (S_NH)', 'Нитраты (S_NO)']
    settings.yLabel = 'Концентрация, мг N/л'
    settings.title = 'ж) Динамика азота (нитрификация/денитрификация)'
    create_plot(settings)
    settings.index += 1

    # ============= 8. Скорость роста бактерий =============
    if settings.index > settings.rows * settings.cols:
        save_figure(f'{settings.fileName} ({settings.fileIndex})')
        create_figure(suptitle)
        settings.index = 1
        settings.fileIndex += 1

    K_S = params['K_S']
    K_OH = params['K_OH']
    mu_H = params['mu_max_H'] * (S_bio / (K_S + S_bio)) * (O / (K_OH + O))
    mu_A = params['mu_max_A'] * (S_NH / (params['K_NH'] + S_NH)) * (O / (params['K_OA'] + O))
    settings.y = [mu_H, mu_A]
    settings.labels = [r'$\mu_H$ (гетеротрофы)', r'$\mu_A$ (автотрофы)']
    settings.yLabel = r'1/день'
    settings.title = 'з) Удельная скорость роста'
    create_plot(settings)

    save_figure(f'{settings.fileName} ({settings.fileIndex})')


def plot_results_v2(sol, params, clarifier_results, ctx=None):
    
    if ctx is None:
        print("no ctx: stop plot_results_v2...")
        return

    tertiary_treatment = ctx.get('tertiary_treatment', None)

    match ctx['model']:
        case 'simple':
            plot_simple(sol, params, clarifier_results, tertiary_treatment)
        case 'with_nitri':
            plot_with_nitri(sol, params, clarifier_results, tertiary_treatment)
        case _:
            print("no model specified in ctx")
            return