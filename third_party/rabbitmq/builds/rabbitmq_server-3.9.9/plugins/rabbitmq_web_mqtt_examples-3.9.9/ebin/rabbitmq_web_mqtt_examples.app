{application, 'rabbitmq_web_mqtt_examples', [
	{description, "Rabbit WEB-MQTT - examples"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_web_mqtt_examples_app']},
	{registered, [rabbitmq_web_mqtt_examples_sup]},
	{applications, [kernel,stdlib,rabbit_common,rabbit,rabbitmq_web_dispatch,rabbitmq_web_mqtt]},
	{mod, {rabbit_web_mqtt_examples_app, []}},
	{env, [
	    {listener, [{port, 15670}]}
	  ]}
]}.