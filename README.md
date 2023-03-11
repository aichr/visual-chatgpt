# Clean Visual ChatGPT 

A cleaner version of [Visual ChatGPT](https://github.com/microsoft/visual-chatgpt/blob/main/README.md).


### Changelog
- remove `assets` folder
- remove `pytorch_lightning` dependency
- remove unused imports
- split the models into `models.py`
- disable most of the torch models to make it work on a single gpu

### Issue
gradio can be instantiated, but hit the following error:

```
Traceback (most recent call last):
  File "/home/tianwei/.local/lib/python3.10/site-packages/gradio/routes.py", line 384, in run_predict
    output = await app.get_blocks().process_api(
  File "/home/tianwei/.local/lib/python3.10/site-packages/gradio/blocks.py", line 1032, in process_api
    result = await self.call_function(
  File "/home/tianwei/.local/lib/python3.10/site-packages/gradio/blocks.py", line 844, in call_function
    prediction = await anyio.to_thread.run_sync(
  File "/home/tianwei/.local/lib/python3.10/site-packages/anyio/to_thread.py", line 31, in run_sync
    return await get_asynclib().run_sync_in_worker_thread(
  File "/home/tianwei/.local/lib/python3.10/site-packages/anyio/_backends/_asyncio.py", line 937, in run_sync_in_worker_thread
    return await future
  File "/home/tianwei/.local/lib/python3.10/site-packages/anyio/_backends/_asyncio.py", line 867, in run
    result = context.run(func, *args)
  File "/home/tianwei/projects/vgpt/vgpt.py", line 284, in run_text
    self.agent.memory.buffer = cut_dialogue_history(
  File "pydantic/main.py", line 358, in pydantic.main.BaseModel.__setattr__
ValueError: "ConversationBufferMemory" object has no field "buffer"
```