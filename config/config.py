import ujson


class ConfigVar:
    value = None
    type_var = None
    default_value = None
    min_value = None
    max_value = None
    init: bool = False

    def __init__(self, value) -> None:
        self.value = value


class Config:
    __values = {}
    __filename_config = 'config.json'

    def __init__(self) -> None:
        try:
            f = open(self.__filename_config, "r")
            values = ujson.load(f)
            f.close()
            for name_var in values:
                self.__values[name_var] = ConfigVar(values[name_var])
        except:
            pass

    def init_var(self, name_var: str, type_var: type, default_value, min_value=None, max_value=None):
        if type_var not in (int, float, bool, str):
            raise Exception(f"Config: тип {type_var} не підтримується для '{name_var}'")
        if type_var in (int, float):
            if min_value is None or max_value is None:
                raise Exception(f"Config: min_value чи max_value не задано для '{name_var}'")
        else:
            if min_value or max_value:
                raise Exception(f"Config: min_value та max_value не підтримується для '{name_var}'")
        
        default_value = type_var(default_value)

        if name_var in self.__values:
            if self.__values[name_var].init:
                raise Exception(f"Config: змінну '{name_var}' вже визначено")
            self.__values[name_var].value = type_var(self.__values[name_var].value)
        else:
            self.__values[name_var] = ConfigVar(default_value)
        self.__values[name_var].init = True
        self.__values[name_var].type_var = type_var
        self.__values[name_var].default_value = default_value
        self.__values[name_var].min_value = min_value
        self.__values[name_var].max_value = max_value
        if min_value and max_value:
            if self.__values[name_var].value < min_value or self.__values[name_var].value > max_value:
                self.__values[name_var].value = default_value
    
    def set_var(self, name_var: str, value):
        if name_var not in self.__values or not self.__values[name_var].init:
            raise Exception(f"Config: змінну '{name_var}' вже визначено")
        if self.__values[name_var].min_value and self.__values[name_var].max_value:
            if value < self.__values[name_var].min_value or value > self.__values[name_var].max_value:
                raise Exception(f"Config: значення '{name_var}' невірне")
        self.__values[name_var].value = self.__values[name_var].type_var(value)
        self._save()
    
    def _save(self):
        values = {}
        for name in self.__values:
            values[name] = self.__values[name].value
        f = open(self.__filename_config, "w")
        ujson.dump(values, f)
        f.close()
    
    def __getattr__(self, __name: str):
        if __name not in self.__values or not self.__values[__name].init:
            raise Exception(f"Config: змінну '{__name}' вже визначено")
        return self.__values[__name].value
