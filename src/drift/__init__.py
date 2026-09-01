"""
Drift Modeling module for SagarDrishti.
Includes forward forecasting and backward hindcasting of oil particle clouds.
"""
try:
    from src.drift.particle_model import initialize_particles
    from src.drift.forward_simulation import simulate_forward
    from src.drift.backward_hindcast import hindcast_origin
except ImportError:
    from .particle_model import initialize_particles
    from .forward_simulation import simulate_forward
    from .backward_hindcast import hindcast_origin

