{application, 'rabbitmq_trust_store', [
	{description, "Client X.509 certificates trust store"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['rabbit_trust_store','rabbit_trust_store_app','rabbit_trust_store_certificate_provider','rabbit_trust_store_file_provider','rabbit_trust_store_http_provider','rabbit_trust_store_sup']},
	{registered, [rabbitmq_trust_store_sup]},
	{applications, [kernel,stdlib,ssl,crypto,public_key,rabbit_common,rabbit]},
	{mod, {rabbit_trust_store_app, []}},
	{env, [
	    {default_refresh_interval, 30},
	    {providers, [rabbit_trust_store_file_provider]}
	  ]}
]}.