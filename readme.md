## Що це?
Це ECU для RC написане на Micropython, Pi pico.
Або простіше можна сказати, що це мозок для радіокерованої моделі.

## Для чого це? Чому Python?
Це керування RC розраховане на максимальну модульність та швидкість розробки та простоту налаштування моделі. 
Так, цей ECU не може похвалитися швидкодією, та для усіх моїх проєктів її вистачає.

## Не простіше, щоб chatGPT написав просте керування?
Простіше. Та все залежить від потреб. 
Цей ECU містить в собі контролер та готові драйвери, модулі.

# Отже почнемо
Все починається з `main.py`. Розпочни зі задання своїх пристроїв, використовуючи драйвери.

### Драйвери – це обгортка, простий інтерфейс для взаємодії з пристроями.

**Щоб використати готові драйвери:**
1. імпортуй драйвер: `from drivers import ServoSG90`;
2. далі потрібно ініціалізувати конкретні пристрої, наприклад для сервоприводу `sg90`: `sg90 = ServoSG90(Pin(29))`. Де `Pin(29)` – пін на який керує сервоприводом;
3. використовувати драйвери в модулях.

Далі потрібно ініціалізувати усі потрібно модулі.

### Модуль – це основна логіка роботи пристроїв.
Тобто драйвер надає функціонал для взаємодії з фізичним пристроєм, 
а модуль містить всю логіку для взаємодії з пристоями або іншими модулями

**Щоб використати готові модулі:**
1. імпортуй модуль: `from drivers import Turn`;
2. далі потрібно ініціалізувати модуль та передати усі драйвери, наприклад, щоб визначити модуль повороту колес: `Turn(sg90)`. Де `sg90` – драйвер сервоприводу;
3. передати модулі у контролер.

Тепер передай усі модулі в контролер та запусти його.

### Контролер запускає, обробляє та надає зв'язок для модулів

**Щоб запустити контролер:**
1. імпортуй контролер: `from controller import Controller`;
2. ініціалізуй контролер, та передай у нього необхідні модулі: `car = Controller(turn)`;
3. запусти контролер: `car.start()`

**У `main.py` вже готовий приклад ініціалізації усіх драйверів, модулів та контролера**






## Розширення функціоналу

**Щоб написати свої драйвери:**
1. імпортуй базовий клас: `from drivers.base import BaseDriver`;
2. далі наслідуй клас `BaseDriver` та пиши будь-який функціонал;
3. в `__init(self)__` обов'язково викликай: `super().__init__()`;
4. для постійного оновлення вкажи атрибут класу `delay_update: int = x`, де `x` мінімальна затримка виклику в мікросекундах;
5. при постійному оновлені викликається метод `__update(self, controller: Controller)`;
6. при запуску контролера викликається метод `_startup(self, controller: Controller)`;
7. при завершенні роботи контролера викликається метод `_shutdown(self, controller: Controller)`;
8. за детальнішою інформацією див. вихідний код

**Щоб написати свої модулі:**
1. імпортуй базовий клас: `from parts.base import BasePart`;
2. далі наслідуй клас `BasePart` та пиши будь-який функціонал;
3. в `__init(self)__` обов'язково викликай: `super().__init__()`;
4. вкажи атрибут класу `delay_update: int = x`, де `x` мінімальна затримка виклику в мікросекундах;
5. при постійному оновлені викликається метод `__update(self, controller: Controller)`;
6. при запуску контролера викликається метод `_startup(self, controller: Controller)`;
7. при завершенні роботи контролера викликається метод `_shutdown(self, controller: Controller)`;
8. за детальнішою інформацією див. вихідний код


**Також є прості способи отримання модулів, комунікації між модулями, збереження та зміни налаштувань, логування тощо. 
Напишу документацію про це, якщо комусь буде цікаво**

PS: багато цікавого є у вбудованих модулях, буде дока, як буде потреба комусь.

Зв'язок в тг: @floms11



## Адреси `Var` вбудованих модулів
### NRF24L01Communication
- `cf` – Канал на якому працює радіомодуль, ціле число від 0 до 125
- `ce` – Pipe радіомодуля, ціле додатнє число (адреса)
- `cd` – Потужність передавача радіомодуля
- `cc` – Швидкість роботи радіомодуля
### Turn
- `a0` – Значення повороту коліс, ціле число від -100 до 100
- `d0` – Позиція серви у крайньому лівому положенні, дробове від 0 до 1
- `d1` – Позиція серви у нейтральному положенні, дробове від 0 до 1
- `d2` – Позиція серви у крайньому правому положенні, дробове від 0 до 1
- `d3` – Квадратні значення повороту коліс (замість лінійних – параболічні)
- `d4` – Система стабілізації
- `d5` – Наскільки різко стабілізація буде реагувати на рухи, ціле число від 1 до 10
- `d6` – Максимальний поворот коліс при 0 швидкості, ціле число від 1 до 10
- `d7` – Максимальний поворот коліс при максимальній швидкості, ціле число від 1 до 10
### Move
- `a1` – Значення прискорення, ціле число від -100 до 100
- `d9` – Квадратні значення прискорення (замість лінійних – параболічні)
### Dashboard
- `b0` – Загальний пробіг в метрах
- `b1` – Швидкість в км/год
- `b2` – Заряд акумулятора у відсотках
- `b3` – Заряд акумулятора у вольтах

### Інші
- `f0` – Радіус колес в мм
- `f1` – Передавальне число від мотора до колес
- `f2` – Максимальна кількість обертів мотора

