from statistics import NormalDist
from currency import Currency

def calc_burn_for_price(curr_ratio, target_ratio, std):
  if curr_ratio < target_ratio:
    return 0.00
  else:
    return NormalDist(target_ratio, std).cdf(curr_ratio)

def calc_start_price(target_ratio):
  return 1/target_ratio

def calc_initial_supply(initial_reserve, target_ratio):
  return initial_reserve * calc_start_price(target_ratio)

class Fundraiser:
  def __init__(self, target_ratio, std, initial_reserve, target_threshold):
    self.currency = Currency(calc_initial_supply(
        initial_reserve, target_ratio), initial_reserve, target_ratio, calc_start_price(target_ratio))
    self.std = std 
    self.target_ratio = target_ratio
    self.target_threshold = target_threshold
  
  def balanced_burn(self, supply_in):
    price_burn = supply_in * \
        calc_burn_for_price(self.currency.r_ratio, self.target_ratio, self.std)
    weight_burn = supply_in - price_burn

    self.currency.burn_change_price(price_burn)
    self.currency.burn_change_weight(weight_burn)
  
  def balanced_burn_reserve(self, reserve_in):
    price_burn = reserve_in * \
        calc_burn_for_price(self.currency.r_ratio, self.target_ratio, self.std)
    weight_burn = reserve_in - price_burn

    self.currency.burn_change_price_reserve(price_burn)
    self.currency.burn_change_weight_reserve(weight_burn)
  
  def accept_revenue(self, reserve_in):
    return self.balanced_burn_reserve(reserve_in)
    
  def get_mintable(self):
    mintable = ((self.currency.r_ratio * self.currency.supply) /
                          (self.target_ratio - self.target_threshold)) - self.currency.supply

    if mintable < 0:
      return 0
    else:
      return mintable

  def invest(self, investment):
    return self.currency.reserve_to_supply(investment)
  
  def divest(self, divestment):
    return self.currency.supply_to_reserve(divestment)