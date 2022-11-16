NON_NATIVE_TRANSFER_FEE = 0.0003
NATIVE_TRANSFER_FEE = 0.0001

def calc_supply_in(curr_supply, curr_reserve, reserve_in, reserve_ratio):
  return curr_supply * ((((reserve_in/curr_reserve) + 1)**(reserve_ratio)) - 1)
  
def calc_reserve_out(curr_reserve, curr_supply, supply_in, reserve_ratio):
  return curr_reserve * (1 - (1 - (supply_in/curr_supply))**(1/reserve_ratio))

def calc_price_in_reserve(reserve, supply, ratio):
  return reserve/(supply*ratio)

def calc_conversion_fees(amount_in, native_source):
  if native_source:
    return (amount_in * 0.00025) + NATIVE_TRANSFER_FEE
  else:
    return (amount_in * 0.00025) + NON_NATIVE_TRANSFER_FEE

class Currency:
  def __init__(self, supply, reserves, r_ratio, start_price):
    self.supply = supply
    self.reserves = reserves
    self.r_ratio = r_ratio
    self.price = start_price
    self.total_fees = 0
    
    self.cap_reserve_ratio()

  def update_price(self):
    self.price = calc_price_in_reserve(self.reserves, self.supply, self.r_ratio)
  
  def cap_reserve_ratio(self):
    self.r_ratio = self.r_ratio

    if self.r_ratio > 1:
      self.r_ratio = 1
  
  def reserve_to_supply(self, reserve_in):
    fees = calc_conversion_fees(reserve_in, True)
    self.total_fees = self.total_fees + fees
    
    conversion_amount = reserve_in - fees

    supply_output = calc_supply_in(self.supply, self.reserves, conversion_amount, self.r_ratio)
    
    self.supply = self.supply + supply_output
    self.reserves = self.reserves + conversion_amount
    self.update_price()

    return supply_output
  
  def prelaunch_carve_out(self, reserve_out):
    old_reserves = self.reserves

    self.reserves = self.reserves - reserve_out
    
    self.r_ratio = self.r_ratio * (self.reserves / old_reserves)
    self.cap_reserve_ratio()
    self.update_price()

    self.total_fees = self.total_fees + NATIVE_TRANSFER_FEE

    return reserve_out - NATIVE_TRANSFER_FEE
    
  def supply_to_reserve(self, supply_in):
    fees = calc_conversion_fees(supply_in, False)
    conversion_amount = supply_in - fees

    reserve_output_amount = calc_reserve_out(self.reserves, self.supply, conversion_amount, self.r_ratio)
    reserve_output_fees = calc_reserve_out(self.reserves, self.supply, fees, self.r_ratio)

    self.reserves = self.reserves - reserve_output_amount + reserve_output_fees
    self.supply = self.supply - supply_in
    self.total_fees = self.total_fees + reserve_output_fees
    self.update_price()

    return reserve_output_amount
  
  def burn_change_price(self, supply_in):
    supply_burned = supply_in - NON_NATIVE_TRANSFER_FEE
    self.total_fees = self.total_fees + self.supply_to_reserve(NON_NATIVE_TRANSFER_FEE)

    self.supply = self.supply - supply_burned
    self.update_price()
  
  def burn_change_weight(self, supply_in):
    old_supply = self.supply

    supply_burned = supply_in - NON_NATIVE_TRANSFER_FEE
    self.total_fees = self.total_fees + self.supply_to_reserve(NON_NATIVE_TRANSFER_FEE)

    self.supply = self.supply - supply_burned

    self.r_ratio = self.r_ratio * (old_supply / self.supply)
    self.cap_reserve_ratio()
    self.update_price()
    
  def mint_change_weight(self, supply_out):
    old_supply = self.supply

    self.total_fees = self.total_fees + self.supply_to_reserve(NON_NATIVE_TRANSFER_FEE)
    self.supply = (self.supply - NON_NATIVE_TRANSFER_FEE) + supply_out

    self.r_ratio = self.r_ratio * (old_supply / self.supply)
    self.cap_reserve_ratio()
    self.update_price()

    return supply_out