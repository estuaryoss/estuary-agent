# Case 1

The agent is running near the SUT. There the test runner can execute SUT actions:
- restart SUT
- copy files
- manage system processes

In such case additional execs can be brought, like jars and called via rest.

![image](https://user-images.githubusercontent.com/43060213/75050738-445e0100-54d5-11ea-884c-859569d72c2d.png)

# Case 2

The agent is controlling the automation framework written in any language.
Here you can instruct the agent to start your specific tests grouped in specific suites.

Examples:
- mvn clean verify -Dtype=GenerateConfig
- mvn clean verify -Dtype=StartTests

This use case applies very well in Kubernetes to have access to the automation framework.

![image](https://user-images.githubusercontent.com/43060213/75050684-25f80580-54d5-11ea-8254-b68b52f45e33.png)

# Case 3

Combine case 1 and 2 together if needed.

# Case 4
Use the agent to control a CLI app via REST API.