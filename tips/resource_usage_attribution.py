from itertools import combinations
from typing import Callable
from typing import Dict
from typing import List
from typing import TypeVar
from typing import Union
from typing import cast
import numpy

# just for type clarity
Resource = TypeVar('Resource')
Service = TypeVar('Service')
Customer = TypeVar('Customer')

# A service can be a provider for other services
Provider = Union[Resource, Service]
Consumer = Union[Service, Customer]

UsageFn = Callable[[Provider, Consumer], float]
Attribution = Dict[Resource, Dict[Consumer, float]]


def attribute_resource_usage(
    resources: List[Resource], services: List[Service],
    customers: List[Customer], usageFn: UsageFn
) -> Attribution:
    '''Attribute the resource usage among the terminal customers of services.

    In this context a Resource is something that is provided out of thin air,
    consumes nothing, and can be consumed by either Services or Customers.
    A Service can consume resources or the output of other services, and
    whose output can be Consumed by other Services or by Customers. A
    Customer can consume resources like a Service, but produces no
    consumable output relevant to this model.

    A Provider is either a Resource or a Service (provides a consumable thing)
    and a Consumer is either a Service or a Consumer (consumes a consumable
    thing).  We require no explicit description of the quantity provided by a
    Service, so long as it is divisible among the clients of the Service.

    The usageFn describes the fraction in [0,1] of the output of each Provider
    that is consumed by each Consumer.

    Each Resource has total supply 1, which can be rescaled by the caller.

    Arguments:
      - resources: a list of Resources
      - services: a list of Services
      - customers: a list of Customers
      - usageFn: a callable accepting as input a Provider (resource/service) P
          and a consuming Consumer (service/customer) U, and produces as output the
          fraction of the total output of P consumed by U. For a fixed P, the sum
          of the outputs of usageFn(P, U) over all users U must be at most 1.

    Returns:
      A dict describing the attribution of each resource among the Customers.
    '''
    # construct transitions among transient states Q
    transient_states = cast(List[Provider], resources) + cast(List[Provider], services)
    Q = resource_service_transition_matrix = numpy.array(
        [[usageFn(a, b) for b in transient_states] for a in transient_states]
    )

    # compute transition to absorbing states
    R = absorbing_state_transition_matrix = numpy.array(
        [[usageFn(a, b) for b in customers] for a in transient_states]
    )

    # invert N = (1-Q)^{-1}
    Q_dim = len(resources) + len(services)
    fundamental_matrix = numpy.linalg.inv(numpy.identity(Q_dim) - Q)

    absorbing_probabilities = numpy.dot(fundamental_matrix, R)

    attribution_dict = {
        resource: {
            customer: absorbing_probabilities[i, j]
            for (j, customer) in enumerate(customers)
        }
        for (i, resource) in enumerate(resources)
    }

    return attribution_dict
