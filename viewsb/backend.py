"""
ViewSB backend class defintions -- defines the abstract base for things that capture USB data.
"""

import multiprocessing





class ViewSBBackendProcess:
    """ Class that controls and communicates with a VSB backend running in another process. """

    def __init__(self, backend_class, *backend_arguments):

        # Create our output queue and our termination-signaling event.
        self.output_queue      = multiprocessing.Queue()
        self.termination_event = multiprocessing.Event()

        self.backend_arguments  = (backend_class, backend_arguments, self.output_queue, self.termination_event)


    def start(self):
        """ Start the background process, and thus the capture. """

        # Ensure our termination event isn't set.
        self.termination_event.clear()

        # Generate a name for our capture process.
        name = "{} capture process".format(self.backend_arguments[0].__name__)

        # Create and start our background process.
        self.background_process = \
            multiprocessing.Process(target=self._subordinate_process_entry, args=self.backend_arguments, name=name)
        self.background_process.start()


    def stop(self):
        """ Halt the background process, and thus the capture. """

        self.termination_event.set()
        self.background_process.join()


    def read_packet(self, blocking=True, timeout=None):
        """ Reads a packet from the background process.

        Args:
            blocking -- If set, the read will block until a packet is available.
            timeout -- The longest time to wait on a blocking read, in floating-point seconds.
        """
        return self.output_queue.get(blocking)


    @staticmethod
    def _subordinate_process_entry(backend_class, arguments, output_queue, termination_event):
        """
        Helper function for running a backend in a blocking manner. This method should usually be called in a subordinate
        process managed by multiprocessing. You probably want the public API of ViewSBBackgroundProcess.
        """

        # Create a new instance of the backend class.
        backend = backend_class(*arguments)

        # Pass the backend our IPC mechanisms.
        backend.set_up_ipc(output_queue, termination_event)

        # Finally, run our backend class until it terminates.
        backend.run()



class ViewSBBackend:
    """ Generic parent class for sources that capture USB data. """


    def __init__(self):
        """
        Function that initializes the relevant backend. In most cases, this objects won't be instantiated
        directly -- but instead instantiated by the `run_asynchronously` / 'run_backend_asynchronously` helpers.
        """
        pass


    def set_up_ipc(self, output_queue, termination_event):
        """
        Function that accepts the synchronization objects we'll use for output. Must be called prior to
        calling run().

        Args:
            output_queue -- The Queue object that will be fed any USB data generated.
            termination_event -- A synchronization event that is set when a capture is terminated.
        """

        # Store our IPC primitives, ready for future use.
        self.output_queue      = output_queue
        self.termination_event = termination_event


    def run_capture(self):
        """ Runs a single iteration of our backend capture. """
        raise NotImplementedError("backends must implement run_capture(), or override run()")


    def emit_packet(self, packet):
        """ Emits a given ViewSBPacket-derivative to the main decoder thread for analysis. """
        self.output_queue.put(packet)


    def run(self):
        """ Runs the given backend until the provided termination event is set. """

        # Capture infinitely until our termination signal is set.
        while not self.termination_event.is_set():
            self.run_capture()

        # Allow the backend to handle any data still pending on termination.
        self.handle_termination()


    def handle_termination(self):
        """ Called once the capture is terminated; gives the backend the ability to capture any remaining data. """
        pass








