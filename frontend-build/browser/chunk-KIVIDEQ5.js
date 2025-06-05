import {
  AnonymousSubject,
  Injectable,
  Observable,
  ReplaySubject,
  Subject,
  Subscriber,
  Subscription,
  setClassMetadata,
  ɵɵdefineInjectable
} from "./chunk-FAGZ4ZSE.js";

// node_modules/rxjs/dist/esm/internal/observable/dom/WebSocketSubject.js
var DEFAULT_WEBSOCKET_CONFIG = {
  url: "",
  deserializer: (e) => JSON.parse(e.data),
  serializer: (value) => JSON.stringify(value)
};
var WEBSOCKETSUBJECT_INVALID_ERROR_OBJECT = "WebSocketSubject.error must be called with an object with an error code, and an optional reason: { code: number, reason: string }";
var WebSocketSubject = class _WebSocketSubject extends AnonymousSubject {
  constructor(urlConfigOrSource, destination) {
    super();
    this._socket = null;
    if (urlConfigOrSource instanceof Observable) {
      this.destination = destination;
      this.source = urlConfigOrSource;
    } else {
      const config = this._config = Object.assign({}, DEFAULT_WEBSOCKET_CONFIG);
      this._output = new Subject();
      if (typeof urlConfigOrSource === "string") {
        config.url = urlConfigOrSource;
      } else {
        for (const key in urlConfigOrSource) {
          if (urlConfigOrSource.hasOwnProperty(key)) {
            config[key] = urlConfigOrSource[key];
          }
        }
      }
      if (!config.WebSocketCtor && WebSocket) {
        config.WebSocketCtor = WebSocket;
      } else if (!config.WebSocketCtor) {
        throw new Error("no WebSocket constructor can be found");
      }
      this.destination = new ReplaySubject();
    }
  }
  lift(operator) {
    const sock = new _WebSocketSubject(this._config, this.destination);
    sock.operator = operator;
    sock.source = this;
    return sock;
  }
  _resetState() {
    this._socket = null;
    if (!this.source) {
      this.destination = new ReplaySubject();
    }
    this._output = new Subject();
  }
  multiplex(subMsg, unsubMsg, messageFilter) {
    const self = this;
    return new Observable((observer) => {
      try {
        self.next(subMsg());
      } catch (err) {
        observer.error(err);
      }
      const subscription = self.subscribe({
        next: (x) => {
          try {
            if (messageFilter(x)) {
              observer.next(x);
            }
          } catch (err) {
            observer.error(err);
          }
        },
        error: (err) => observer.error(err),
        complete: () => observer.complete()
      });
      return () => {
        try {
          self.next(unsubMsg());
        } catch (err) {
          observer.error(err);
        }
        subscription.unsubscribe();
      };
    });
  }
  _connectSocket() {
    const {
      WebSocketCtor,
      protocol,
      url,
      binaryType
    } = this._config;
    const observer = this._output;
    let socket = null;
    try {
      socket = protocol ? new WebSocketCtor(url, protocol) : new WebSocketCtor(url);
      this._socket = socket;
      if (binaryType) {
        this._socket.binaryType = binaryType;
      }
    } catch (e) {
      observer.error(e);
      return;
    }
    const subscription = new Subscription(() => {
      this._socket = null;
      if (socket && socket.readyState === 1) {
        socket.close();
      }
    });
    socket.onopen = (evt) => {
      const {
        _socket
      } = this;
      if (!_socket) {
        socket.close();
        this._resetState();
        return;
      }
      const {
        openObserver
      } = this._config;
      if (openObserver) {
        openObserver.next(evt);
      }
      const queue = this.destination;
      this.destination = Subscriber.create((x) => {
        if (socket.readyState === 1) {
          try {
            const {
              serializer
            } = this._config;
            socket.send(serializer(x));
          } catch (e) {
            this.destination.error(e);
          }
        }
      }, (err) => {
        const {
          closingObserver
        } = this._config;
        if (closingObserver) {
          closingObserver.next(void 0);
        }
        if (err && err.code) {
          socket.close(err.code, err.reason);
        } else {
          observer.error(new TypeError(WEBSOCKETSUBJECT_INVALID_ERROR_OBJECT));
        }
        this._resetState();
      }, () => {
        const {
          closingObserver
        } = this._config;
        if (closingObserver) {
          closingObserver.next(void 0);
        }
        socket.close();
        this._resetState();
      });
      if (queue && queue instanceof ReplaySubject) {
        subscription.add(queue.subscribe(this.destination));
      }
    };
    socket.onerror = (e) => {
      this._resetState();
      observer.error(e);
    };
    socket.onclose = (e) => {
      if (socket === this._socket) {
        this._resetState();
      }
      const {
        closeObserver
      } = this._config;
      if (closeObserver) {
        closeObserver.next(e);
      }
      if (e.wasClean) {
        observer.complete();
      } else {
        observer.error(e);
      }
    };
    socket.onmessage = (e) => {
      try {
        const {
          deserializer
        } = this._config;
        observer.next(deserializer(e));
      } catch (err) {
        observer.error(err);
      }
    };
  }
  _subscribe(subscriber) {
    const {
      source
    } = this;
    if (source) {
      return source.subscribe(subscriber);
    }
    if (!this._socket) {
      this._connectSocket();
    }
    this._output.subscribe(subscriber);
    subscriber.add(() => {
      const {
        _socket
      } = this;
      if (this._output.observers.length === 0) {
        if (_socket && (_socket.readyState === 1 || _socket.readyState === 0)) {
          _socket.close();
        }
        this._resetState();
      }
    });
    return subscriber;
  }
  unsubscribe() {
    const {
      _socket
    } = this;
    if (_socket && (_socket.readyState === 1 || _socket.readyState === 0)) {
      _socket.close();
    }
    this._resetState();
    super.unsubscribe();
  }
};

// node_modules/rxjs/dist/esm/internal/observable/dom/webSocket.js
function webSocket(urlConfigOrSource) {
  return new WebSocketSubject(urlConfigOrSource);
}

// src/app/services/websocket.service.ts
var WebsocketService = class _WebsocketService {
  constructor() {
    this.toastMessage = new Subject();
    this.connect();
  }
  connect() {
    if (!this.socket$ || this.socket$.closed) {
      const client_id = Math.floor(Math.random() * 1e6);
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const hostname = window.location.hostname;
      const port = window.location.port ? `:${window.location.port}` : "";
      const wsUrl = `${wsProtocol}//${hostname}${port}/ws/${client_id}`;
      this.socket$ = webSocket(wsUrl);
      this.websocketSubscription = this.socket$.subscribe({
        next: (data) => {
          this.toastMessage.next(data);
        },
        error: (error) => {
          console.error("WebSocket error:", error);
        },
        complete: () => {
          console.log("WebSocket connection closed");
        }
      });
    }
    return this.socket$.asObservable();
  }
  showToast(message, type = "Success") {
    this.toastMessage.next({ message, type });
  }
  close() {
    if (this.websocketSubscription) {
      this.websocketSubscription.unsubscribe();
    }
    this.socket$.complete();
  }
  static {
    this.\u0275fac = function WebsocketService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _WebsocketService)();
    };
  }
  static {
    this.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({ token: _WebsocketService, factory: _WebsocketService.\u0275fac, providedIn: "root" });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(WebsocketService, [{
    type: Injectable,
    args: [{
      providedIn: "root"
    }]
  }], () => [], null);
})();

export {
  WebsocketService
};
//# sourceMappingURL=chunk-KIVIDEQ5.js.map
