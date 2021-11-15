{application, 'amqp10_client', [
	{description, "AMQP 1.0 client from the RabbitMQ Project"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['amqp10_client','amqp10_client_app','amqp10_client_connection','amqp10_client_connection_sup','amqp10_client_connections_sup','amqp10_client_frame_reader','amqp10_client_session','amqp10_client_sessions_sup','amqp10_client_sup','amqp10_client_types','amqp10_msg']},
	{registered, [amqp10_client_sup]},
	{applications, [kernel,stdlib,ssl,inets,crypto,amqp10_common]},
	{mod, {amqp10_client_app, []}},
	{env, []}
]}.