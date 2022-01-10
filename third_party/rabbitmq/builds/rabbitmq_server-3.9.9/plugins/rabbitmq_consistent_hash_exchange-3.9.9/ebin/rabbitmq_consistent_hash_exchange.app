{application, 'rabbitmq_consistent_hash_exchange', [
	{description, "Consistent Hash Exchange Type"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['Elixir.RabbitMQ.CLI.Diagnostics.Commands.ConsistentHashExchangeRingStateCommand','rabbit_exchange_type_consistent_hash']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit]},
	{env, []},
		{broker_version_requirements, []}
]}.