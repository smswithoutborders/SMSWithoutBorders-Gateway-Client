{application, 'rabbitmq_recent_history_exchange', [
	{description, "RabbitMQ Recent History Exchange"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_exchange_type_recent_history']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit]},
	{env, []},
		{broker_version_requirements, []}
]}.