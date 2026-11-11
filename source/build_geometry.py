import json, os
root='/mnt/data/apartment3d'
# Coordinates are pixels read from measurements.jpg. 100.5 px ≈ 1 m from 3.17x3.84 and 4.23x3.27 dimensions.
rooms = [
 dict(id='bedroom', name='Комната 12,2',use='Спальня (демонстрационная расстановка)', area='12,2',dims='3,17 × 3,84 м',color='#cdbba9',polygon=[[438,36],[756,36],[756,421],[438,421]], label=[593,222],furniture='bedroom'),
 dict(id='kitchen', name='Кухня 15,4',use='Кухня и обеденная зона',area='15,4',dims='4,54 × 3,47 м',color='#d6cbb8',polygon=[[182,438],[637,438],[637,781],[182,781]],label=[390,591],furniture='kitchen'),
 dict(id='living', name='Комната 13,8',use='Гостиная (демонстрационная расстановка)',area='13,8',dims='4,23 × 3,27 м',color='#c5c4b6',polygon=[[182,800],[606,800],[606,1129],[182,1129]],label=[396,964],furniture='living'),
 dict(id='hall', name='Коридор 7,8',use='Прихожая и проходная часть',area='7,8',dims='1,29 × 3,57 м + входная часть',color='#d9d0bc',polygon=[[646,434],[775,434],[775,795],[794,795],[794,971],[614,971],[614,795],[646,795]],label=[707,684],furniture='hall'),
 dict(id='bath', name='Ванная',use='Ванна / раковина',area='≈ 3,5',dims='Около 1,73 × 2,03 м',color='#b1c9cc',polygon=[[784,438],[960,438],[960,642],[784,642]],label=[865,553],furniture='bath'),
 dict(id='wc', name='Санузел',use='Туалет',area='уточнить',dims='Контуры уточняются: планы расходятся',color='#b5c9cb',polygon=[[784,651],[960,651],[960,780],[784,780]],label=[864,711],furniture='wc'),
 dict(id='closet', name='Гардеробная',use='Система хранения',area='1,8',dims='1,17 × 1,51 м',color='#c8beab',polygon=[[619,982],[744,982],[744,1129],[619,1129]],label=[681,1060],furniture='closet'),
 dict(id='balcony', name='Лоджия',use='Открытая лоджия',area='3,4',dims='Размер по контуру чертежа',color='#adb6ae',polygon=[[162,272],[402,272],[402,414],[162,414]],label=[279,342],furniture='balcony'),
]
# Walls: centerlines and openings in original source pixel coordinates.
# We mark some door/window opening lengths as reference-plan estimates because the survey drawing does not dimension them.
walls=[
 dict(id='w_top_n',a=[422,20],b=[771,20],type='exterior',holes=[dict(a=510,b=691,type='window',note='Окно: положение с обмерного плана')]),
 dict(id='w_top_w',a=[422,20],b=[422,423],type='exterior'),
 dict(id='w_top_e',a=[770,20],b=[770,425],type='interior'),
 dict(id='w_top_s',a=[426,426],b=[771,426],type='interior',holes=[dict(a=660,b=750,type='door',note='Проём перенесён с первого плана')]),
 dict(id='w_k_n1',a=[165,423],b=[407,423],type='exterior',holes=[dict(a=266,b=363,type='balcony',note='Выход на лоджию с первого плана')]),
 dict(id='w_k_n2',a=[408,425],b=[643,425],type='interior'),
 dict(id='w_k_w',a=[166,423],b=[166,791],type='exterior',holes=[dict(a=511,b=559,type='window',note='Ширина окна на втором плане отображена неоднозначно')]),
 dict(id='w_k_e',a=[643,428],b=[643,790],type='interior',holes=[dict(a=540,b=625,type='door',note='Проём перенесён с первого плана')]),
 dict(id='w_dividing',a=[168,792],b=[644,792],type='interior'),
 dict(id='w_l_w',a=[166,792],b=[166,1143],type='exterior',holes=[dict(a=877,b=1057,type='window',note='Окно по обмерному плану')]),
 dict(id='w_l_s',a=[166,1143],b=[612,1143],type='exterior'),
 dict(id='w_l_e',a=[612,793],b=[612,1140],type='interior',holes=[dict(a=812,b=901,type='door',note='Дверь по первому плану')]),
 dict(id='w_bath_n',a=[777,427],b=[971,427],type='interior'),
 dict(id='w_bath_e',a=[971,427],b=[971,791],type='exterior'),
 dict(id='w_bath_h',a=[777,645],b=[971,645],type='interior'),
 dict(id='w_wc_s',a=[777,789],b=[971,789],type='interior'),
 dict(id='w_h_e',a=[777,428],b=[777,788],type='interior',holes=[dict(a=526,b=603,type='door',note='Дверь ванной: положение уточнить'),dict(a=688,b=752,type='door',note='Дверь санузла: положение уточнить')]),
 dict(id='w_entry_e',a=[803,797],b=[803,972],type='interior',holes=[dict(a=818,b=908,type='entry',note='Входная дверь: первый план')]),
 dict(id='w_entry_s',a=[744,976],b=[808,976],type='interior'),
 dict(id='w_closet_n',a=[612,978],b=[749,978],type='interior',holes=[dict(a=625,b=707,type='door',note='Проём гардеробной по первому плану')]),
 dict(id='w_closet_e',a=[750,978],b=[750,1141],type='interior'),
 dict(id='w_closet_s',a=[612,1141],b=[752,1141],type='exterior'),
 # Loggia parapets and rails, not full-height walls
 dict(id='w_log_w',a=[159,268],b=[159,421],type='rail'),
 dict(id='w_log_n',a=[159,270],b=[409,270],type='rail'),
 dict(id='w_log_s1',a=[159,420],b=[266,420],type='parapet'),
 dict(id='w_log_s2',a=[364,420],b=[421,420],type='parapet'),
]
assumptions=[
 'Высота стен 2,72 м принята для визуализации: отметка потолка на плане отсутствует.',
 'Размеры дверных проёмов восстановлены по первому плану, не являются обмерными.',
 'Правый верхний блок помещений второго чертежа не включён: он отсутствует в первом плане и предположительно относится к соседнему объекту.',
 'Площадь санузла и точные конфигурации сантехнических ниш расходятся между схемами.',
 'Толщина стен и высота подоконников ориентировочны: на изображениях нет полного набора соответствующих размеров.',
 'Мебель — пример дизайна, а не часть исходных обмеров.'
]
data=dict(source='Обмерный план (второе изображение) + расположение дверей из первого изображения',calibration=dict(pixels_per_meter=100.5,x0=0,z0=0,method='Калибровка по размерам 3,17×3,84 и 4,23×3,27'),wall_height_m=2.72,rooms=rooms,walls=walls,assumptions=assumptions)
with open(root+'/data/geometry.json','w',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
print('geometry',len(rooms),'rooms',len(walls),'walls')
