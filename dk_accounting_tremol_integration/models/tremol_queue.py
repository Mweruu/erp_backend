from time import sleep

from odoo import models, fields, _, api

import logging
import time
import requests
import json
import threading
import uuid
from queue import Queue
from threading import Thread, Lock

_logger = logging.getLogger(__name__)

class RequestItem:
    def __init__(self, request_id, messages, company_vat, response_queue):
        self.request_id = request_id
        self.messages = messages
        self.company_vat = company_vat
        self.response_queue = response_queue

class TremolQueueDriver:
    def __init__(self):
        self.queues = {}  # Dictionary to hold queues per URL
        self.threads = {}
        self.lock = Lock()
        self.queue_events = {}

    def start_thread_for_url(self, url):
        with self.lock:
            if url not in self.queues:
                # Create a new queue and event for the new URL
                self.queues[url] = Queue()
                self.queue_events[url] = threading.Event()

                # Start a new thread for the new URL
                thread = Thread(target=self.run, args=(url,))
                thread.daemon = True
                thread.start()

                self.threads[url] = thread
                _logger.info(f"Started new thread for URL: {url}")

    def push_task(self, url, task):
        self.start_thread_for_url(url)  # Ensure a thread and queue exist for this URL
        self.queues[url].put(task)
        self.queue_events[url].set()  # Signal the worker thread for this URL

    def process_request(self, messages, company_vat, url, request_id):
        response = {"status": "Not"}
        data = {
            'messages': messages,
            'company_vat': company_vat
        }
        start_time = time.time()  # Start time measurement
        try:
            _logger.info(f"wake Starting processing request for {request_id} at {url}")
            time.sleep(15)
            response = requests.post(url, data=data)
            response.raise_for_status()
            response_json = response.json()
        except requests.exceptions.RequestException as e:
            response_json = {'message': str(e), 'status': 'Failed'}
            _logger.error(response_json)
        except Exception as e:
            response_json = {'message': str(e), 'status': 'Failed'}
            _logger.error(response_json)
        finally:
            end_time = time.time()  # End time measurement
            elapsed_time = end_time - start_time
            _logger.error("POS Tremol time %s", elapsed_time)
            _logger.error(f"Finished processing request for {request_id} at {url} in {elapsed_time:.2f} seconds")

        return response_json

    def run(self, url):
        while True:
            self.queue_events[url].wait()  # Wait for tasks to be queued
            queue = self.queues[url]
            while not queue.empty():
                item = queue.get()
                if item is None:
                    return
                response = self.process_request(item.messages, item.company_vat, url, item.request_id)
                item.response_queue.put(response)
                queue.task_done()

            if queue.empty():
                self.queue_events[url].clear()  # Reset the event only after the queue is empty

class QueueTremol(models.Model):
    _name = 'tremol.queue'
    _description = "tremol queue"

    @api.model
    def queue_tremol(self, url, messages, company_vat):
        request_id = str(uuid.uuid4())
        response_queue = Queue()
        item = RequestItem(request_id, messages, company_vat, response_queue)
        driver.push_task(url, item)  # Push the task to the specific URL's queue
        try:
            response = item.response_queue.get(timeout=200)
            _logger.info("Received response for %s %s ", item.request_id, json.dumps(response))
        except response_queue.empty():
            _logger.info("Received response exception for %s", item.request_id)
            response = json.dumps({'status': 'Request timed out'})

        return json.dumps(response)

# Initialize the driver (without predefined URLs)
driver = TremolQueueDriver()