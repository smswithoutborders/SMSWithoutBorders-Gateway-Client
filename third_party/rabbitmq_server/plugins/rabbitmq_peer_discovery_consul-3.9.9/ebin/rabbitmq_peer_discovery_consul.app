{application, 'rabbitmq_peer_discovery_consul', [
	{description, "Consult-based RabbitMQ peer discovery backend"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_peer_discovery_consul','rabbitmq_peer_discovery_consul','rabbitmq_peer_discovery_consul_app','rabbitmq_peer_discovery_consul_health_check_helper','rabbitmq_peer_discovery_consul_sup']},
	{registered, [rabbitmq_peer_discovery_consul_sup]},
	{applications, [kernel,stdlib,rabbit_common,rabbitmq_peer_discovery_common,rabbit]},
	{mod, {rabbitmq_peer_discovery_consul_app, []}},
	{env, []}
]}.