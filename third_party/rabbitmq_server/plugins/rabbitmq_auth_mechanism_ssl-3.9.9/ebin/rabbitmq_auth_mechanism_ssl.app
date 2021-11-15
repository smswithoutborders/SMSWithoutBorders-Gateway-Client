{application, 'rabbitmq_auth_mechanism_ssl', [
	{description, "RabbitMQ SSL authentication (SASL EXTERNAL)"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_auth_mechanism_ssl','rabbit_auth_mechanism_ssl_app']},
	{registered, [rabbitmq_auth_mechanism_ssl_sup]},
	{applications, [kernel,stdlib,rabbit_common,rabbit]},
	{mod, {rabbit_auth_mechanism_ssl_app, []}},
	{env, [
	    {name_from, distinguished_name}
	  ]},
		{broker_version_requirements, []}
]}.