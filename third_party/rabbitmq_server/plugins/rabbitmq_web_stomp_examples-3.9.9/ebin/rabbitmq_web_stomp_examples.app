{application, 'rabbitmq_web_stomp_examples', [
	{description, "Rabbit WEB-STOMP - examples"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_web_stomp_examples_app']},
	{registered, [rabbitmq_web_stomp_examples_sup]},
	{applications, [kernel,stdlib,rabbit_common,rabbit,rabbitmq_web_dispatch,rabbitmq_web_stomp]},
	{mod, {rabbit_web_stomp_examples_app, []}},
	{env, [
	    {listener, [{port, 15670}]}
	  ]}
]}.