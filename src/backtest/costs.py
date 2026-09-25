def check_costs(fee, slippage):
    import math
    if not all(math.isfinite(x) and 0 <= x < 1 for x in (fee,slippage)):
        raise ValueError("Costs must be finite and in [0,1)")

def buy_units(cash, opening, fee, slippage):
    price=opening*(1+slippage)
    units=cash/(price*(1+fee))
    return units, units*price*fee, price

def sell_value(units, opening, fee, slippage):
    price=opening*(1-slippage)
    charge=units*price*fee
    return units*price-charge, charge, price
