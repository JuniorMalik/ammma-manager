import math
from dataclasses import dataclass
from typing import Optional

@dataclass
class PrintSettings:
    filament_price_kg: float = 55.0  # R$ por kg
    electricity_cost_h: float = 0.11 # R$ por hora (estimado da planilha)
    printer_depreciation_h: float = 0.58 # R$ por hora (estimado da planilha)
    labor_rate_h: float = 20.0       # R$ por hora de trabalho humano
    buffer_margin: float = 0.1       # 10% de margem de erro/segurança
    markup_factor: float = 2.0       # 2x sobre o custo final para venda sugerida

class CostCalculator:
    def __init__(self, settings: PrintSettings = PrintSettings()):
        self.settings = settings

    def calculate(
        self, 
        weight_g: float, 
        time_hours: float, 
        labor_hours: float = 0, 
        consumables: float = 0, 
        packaging: float = 0
    ) -> dict:
        # 1. Custo de Filamento
        filament_cost = (weight_g / 1000) * self.settings.filament_price_kg
        
        # 2. Custo de Eletricidade
        electricity_cost = time_hours * self.settings.electricity_cost_h
        
        # 3. Custo da Impressora (Depreciação/Manutenção)
        printer_cost = time_hours * self.settings.printer_depreciation_h
        
        # 4. Custo de Trabalho (Humano)
        labor_cost = labor_hours * self.settings.labor_rate_h
        
        # 5. Subtotal
        subtotal = filament_cost + electricity_cost + printer_cost + labor_cost + consumables + packaging
        
        # 6. Custo Final (com margem de segurança de 10%)
        final_cost = subtotal * (1 + self.settings.buffer_margin)
        
        # 7. Venda Sugerida
        suggested_sale = final_cost * self.settings.markup_factor
        
        return {
            "filament_cost": round(filament_cost, 2),
            "electricity_cost": round(electricity_cost, 2),
            "printer_cost": round(printer_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "subtotal": round(subtotal, 2),
            "final_cost": round(final_cost, 2),
            "suggested_sale": round(suggested_sale, 2),
            "profit": round(suggested_sale - final_cost, 2)
        }

if __name__ == "__main__":
    # Teste baseado na linha 13 da planilha (Bandeja das mães fofa)
    calc = CostCalculator()
    result = calc.calculate(weight_g=320, time_hours=4.5, packaging=5)
    print("Teste Bandeja das mães:")
    for k, v in result.items():
        print(f"{k}: R$ {v}")
