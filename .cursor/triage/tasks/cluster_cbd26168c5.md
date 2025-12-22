# Cluster cbd26168c5

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `failed on setup with "file massgen/tests/memory/test_context_window_management.py, line <line>
  async def test_with_persistent_memory(config: dict):
      """Test context compression with persistent memory enabled."""
      # Check if memory is enabled in config
      memory_config = config.get("memory", {})
      if not memory_config.get("enabled", True):
          print("\n⚠️  Skipping: memory.enabled is false in config")
          return

      persistent_enabled = memory_config.get("persistent_memory", {}).get("enabled", True)
      if not persistent_enabled:
          print("\n⚠️  Skipping: memory.persistent_memory.enabled is false in config")
          return

      print("\n" + "=" * 70)
      print("TEST 1: Context Window Management WITH Persistent Memory")
      print("=" * 70 + "\n")

      # Get memory settings from config
      persistent_config = memory_config.get("persistent_memory", {})
      agent_name = persistent_config.get("agent_name", "storyteller_agent")
      session_name = persistent_config.get("session_name", "test_session")
      on_disk = persistent_config.get("on_disk", True)

      # Create LLM backend for both agent and memory
      llm_backend = ChatCompletionsBackend(
          type="openai",
          model="gpt-4o-mini",  # Use smaller model for faster testing
          api_key=os.getenv("OPENAI_API_KEY"),
      )

      # Create embedding backend for persistent memory
      embedding_backend = ChatCompletionsBackend(
          type="openai",
          model="text-embedding-3-small",
          api_key=os.getenv("OPENAI_API_KEY"),
      )

      # Initialize memory systems
      conversation_memory = ConversationMemory()
      persistent_memory = PersistentMemory(
          agent_name=agent_name,
          session_name=session_name,
          llm_backend=llm_backend,
          embedding_backend=embedding_backend,
          on_disk=on_disk,
      )

      # Create agent with memory
      agent = SingleAgent(
          backend=llm_backend,
          agent_id="storyteller",
          system_message="You are a creative storyteller. Create detailed, " "immersive narratives with rich descriptions.",
          conversation_memory=conversation_memory,
          persistent_memory=persistent_memory,
      )

      print("✅ Agent initialized with memory")
      print("   - ConversationMemory: Active")
      print(f"   - PersistentMemory: Active (agent={agent_name}, session={session_name}, on_disk={on_disk})")
      print("   - Model context window: <n>,<n> tokens")
      print("   - Compression triggers at: 96,<n> tokens (75%)")
      print("   - Target after compression: 51,<n> tokens (40%)\n")

      # Simulate a conversation that will fill context
      # Each turn will add significant tokens
      story_prompts = [
          "Tell me the beginning of a space exploration story. Include details about the ship, crew, and their mission. (Make it <n>+ words)",
          "What happens when they encounter their first alien planet? Describe it in vivid detail.",
          "Describe a tense first contact situation with aliens. What do they look like? How do they communicate?",
          "The mission takes an unexpected turn. What crisis occurs and how does the crew respond?",
          "Show me a dramatic action sequence involving the ship's technology and the alien environment.",
          "Reveal a plot twist about one of the crew members or the mission itself.",
          "Continue the story with escalating tension and more discoveries.",
          "How do cultural differences between humans and aliens create conflicts?",
          "Describe a major decision point for the crew captain. What are the stakes?",
          "Bring the story to a climactic moment with high drama.",
      ]

      turn = 0
      for prompt in story_prompts:
          turn += 1
          print(f"\n--- Turn {turn} ---")
          print(f"User: {prompt}\n")

          response_text = ""
          async for chunk in agent.chat([{"role": "user", "content": prompt}]):
              if chunk.type == "content" and chunk.content:
                  response_text += chunk.content

          print(f"Agent: {response_text[:<n>]}...")
          print(f"       [{len(response_text)} chars in response]")

          # Check if compression occurred by examining conversation size
          if conversation_memory:
              size = await conversation_memory.size()
              print(f"       [Conversation memory: {size} messages]\n")

      print("\n✅ Test completed!")
      print("   Check the output above for compression logs:")
      print("   - Look for: '#x1F4CA Context usage: ...'")
      print("   - Look for: '#x1F4E6 Compressed N messages into long-term memory'")
E       fixture 'config' not found
>       available fixtures: _class_scoped_runner, _function_scoped_runner, _module_scoped_runner, _package_scoped_runner, _session_scoped_runner, anyio_backend, anyio_backend_name, anyio_backend_options, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, capteesys, doctest_namespace, event_loop_policy, free_tcp_port, free_tcp_port_factory, free_udp_port, free_udp_port_factory, monkeypatch, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, subtests, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
>       use 'pytest --fixtures [testpath]' for help on them.

massgen/tests/memory/test_context_window_management.py:45"`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/memory/test_context_window_management.py::test_with_persistent_memory
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/memory/test_context_window_management.py::test_with_persistent_memory
```

## Affected nodeids

- `massgen/tests/memory/test_context_window_management.py::test_with_persistent_memory`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

