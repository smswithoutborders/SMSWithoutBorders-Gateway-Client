{application, 'rabbitmq_auth_backend_oauth2', [
	{description, "OAuth 2 and JWT-based AuthN and AuthZ backend"},
	{vsn, "3.9.9"},
	{id, "v3.9.8-33-g5b0ceaa"},
	{modules, ['Elixir.RabbitMQ.CLI.Ctl.Commands.AddUaaKeyCommand','rabbit_auth_backend_oauth2','rabbit_auth_backend_oauth2_app','rabbit_oauth2_scope','uaa_jwt','uaa_jwt_jwk','uaa_jwt_jwt','wildcard']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit,cowlib,jose,base64url]},
	{env, []}
]}.