{application, 'rabbitmq_jms_topic_exchange', [
	{description, "RabbitMQ JMS topic selector exchange plugin"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_jms_topic_exchange','sjx_evaluator']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit]},
	{env, []}
]}.