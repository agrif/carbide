from carbide.scene.json import Data, Enum, TypedSerializable


class Integrator(TypedSerializable, Data):
    min_bounces: int = 0
    max_bounces: int = 64
    enable_consistency_checks: bool = False
    enable_two_sided_shading: bool = True


class PathTracer(Integrator):
    type = 'path_tracer'
    enable_light_sampling: bool = True
    enable_volume_light_sampling: bool = True
    low_order_scattering: bool = True
    include_surfaces: bool = True


class LightTracer(Integrator):
    type = 'light_tracer'
    low_order_scattering: bool = True
    include_surfaces: bool = True


class VolumePhotonType(Enum):
    POINTS = object()
    BEAMS = object()
    PLANES = object()
    PLANES_1D = object()


class PhotonMap(Integrator):
    type = 'photon_map'
    photon_count: int = 1000000
    volume_photon_count: int = 1000000
    gather_photon_count: int = 20
    volume_photon_type: VolumePhotonType = VolumePhotonType.POINTS
    gather_radius: float = 1.0e30
    volume_gather_radius: float = 1.0e30
    low_order_scattering: bool = True
    include_surfaces: bool = True
    fixed_volume_radius: bool = False
    use_grid: bool = False
    use_frustrum_grid: bool = False
    # in kB
    grid_memory: int = 32 * 1024


class ProgressivePhotonMap(PhotonMap):
    type = 'progressive_photon_map'
    alpha: float = 0.3


class BidirectionalPathTracer(Integrator):
    type = 'bidirectional_path_tracer'
    image_pyramid: bool = False


class KelemenMlt(Integrator):
    type = 'kelemen_mlt'
    initial_sample_pool: int = 10000
    bidirectional: bool = True
    large_step_probability: float = 0.1
    image_pyramid: bool = False


class MultiplexedMlt(Integrator):
    type = 'multiplexed_mlt'
    initial_sample_pool: int = 3000000
    large_step_probability: float = 0.1
    image_pyramid: bool = False


class ReversibleJumpMlt(Integrator):
    type = 'reversible_jump_mlt'
    initial_sample_pool: int = 3000000
    iterations_per_batch: int = -1
    large_step_probability: float = 0.1
    strategy_perturbation_probability: float = 0.05
    gaussian_mutation: bool = False
    image_pyramid: bool = False
