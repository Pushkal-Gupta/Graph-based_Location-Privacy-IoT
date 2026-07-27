# Energy-Model Sensitivity Report

The paper's baseline uses a LoRa-class radio (5 mJ/report), under which radio transmission dominates (98--99 % of energy) and the mechanism ranking by energy is essentially flat. This report shows how that picture changes with the radio technology.

## Radio-energy fraction by technology

| Radio | E_radio (mJ) | Min radio fraction | Max radio fraction |
|-------|:------------:|:------------------:|:------------------:|
| BLE | 0.05 | 6.0% | 50.0% |
| Zigbee | 0.35 | 30.9% | 87.5% |
| LoRa | 5.00 | 86.5% | 99.0% |
| NB-IoT | 60.00 | 98.7% | 99.9% |
| LTE-M | 75.00 | 99.0% | 99.9% |

## Key finding

- Under **LoRa/NB-IoT/LTE-M** (LPWAN & cellular), radio energy is 5--75 mJ, so computation (<1 mJ) is negligible and the paper's 'radio dominates' claim holds.
- Under **BLE (0.05 mJ)**, computation is *comparable to or larger than* radio for the BFS-based mechanisms (k-anonymity, density-aware), so the 'radio dominates' claim **does not hold** and the energy ranking is led by the lightweight mechanisms (DP, temporal cloaking).
- Therefore the headline is scoped to LPWAN/cellular deployments; for short-range radios, algorithm computation is a first-order energy factor.

## Energy ranking (cheapest first) by radio

- **BLE**: eps1.0_w600 < k3_w600 < k2_w600 < eps1.0_w600 < k3_w600 < w600
- **Zigbee**: eps1.0_w600 < k3_w600 < k2_w600 < eps1.0_w600 < k3_w600 < w600
- **LoRa**: eps1.0_w600 < k3_w600 < k2_w600 < eps1.0_w600 < k3_w600 < w600
- **NB-IoT**: eps1.0_w600 < k3_w600 < k2_w600 < eps1.0_w600 < k3_w600 < w600
- **LTE-M**: eps1.0_w600 < k3_w600 < k2_w600 < eps1.0_w600 < k3_w600 < w600
