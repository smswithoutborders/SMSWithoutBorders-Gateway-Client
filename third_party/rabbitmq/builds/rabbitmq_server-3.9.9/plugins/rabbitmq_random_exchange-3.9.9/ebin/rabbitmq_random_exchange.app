{application, 'rabbitmq_random_exchange', [
	{description, "RabbitMQ Random Exchange"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_exchange_type_random']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit]},
	{env, []}
]}.