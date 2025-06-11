import { useState, useRef, useEffect } from 'react'
import { Button } from './components/ui/button'
import { Trash2, Download, Upload, Github, Terminal, Server, Monitor, Cpu } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './components/ui/tooltip'

interface Command {
  id: number
  command: string
  response: string
  timestamp: string
}

interface Sequence {
  id: number
  received: string
  response: string
}

interface Log {
  id: number
  message: string
  timestamp: string
}

interface SystemStatus {
  backend: {
    status: boolean;
    port: number;
  };
  frontend: {
    status: boolean;
    port: number;
  };
  driver: {
    status: boolean;
    device: string;
  };
}

function App() {
  const [isRunning, setIsRunning] = useState(false)
  const [deviceExists, setDeviceExists] = useState(false)
  const [config, setConfig] = useState({
    device_path: '/dev/spi_test',
    bus_num: 0,
    cs_num: 0,
    speed: 1000000,
    mode: 0,
    bits_per_word: 8
  })
  const [command, setCommand] = useState('')
  const [commandList, setCommandList] = useState<Command[]>([])
  const [sequence, setSequence] = useState<Sequence[]>([])
  const [newReceived, setNewReceived] = useState('')
  const [newResponse, setNewResponse] = useState('')
  const [logList, setLogList] = useState<Log[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const terminalRef = useRef<HTMLDivElement>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    backend: { status: false, port: 5001 },
    frontend: { status: false, port: 5173 },
    driver: { status: false, device: '/dev/spi_test' }
  });

  const handleConfigChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({
      ...config,
      [field]: event.target.value
    })
  }

  const handleSaveConfig = async () => {
    try {
      // Extract device name from device path
      const deviceName = config.device_path.replace('/dev/', '');
      const requestBody = {
        device_name: deviceName,
        ...config
      };
      
      console.log('Sending config to backend:', requestBody);
      
      const response = await fetch('http://localhost:5001/api/spi/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })
      const data = await response.json()
      console.log('Config saved:', data)
    } catch (error) {
      console.error('Error saving config:', error)
    }
  }

  const handleSendCommand = async () => {
    if (!command.trim()) return

    try {
      const response = await fetch('http://localhost:5001/api/spi/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command }),
      })
      const data = await response.json()
      
      const newCommand: Command = {
        id: Date.now(),
        command: command,
        response: data.response,
        timestamp: new Date().toLocaleTimeString()
      }
      
      setCommandList(prev => [...prev, newCommand])
      setCommand('')
    } catch (error) {
      console.error('Error sending command:', error)
    }
  }

  const handleAddSequence = async () => {
    if (!newReceived.trim() || !newResponse.trim()) return

    const newSeq: Sequence = {
      id: Date.now(),
      received: newReceived,
      response: newResponse
    }

    try {
      // Send sequences to backend
      const response = await fetch('http://localhost:5001/api/spi/sequences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify([...sequence, newSeq]),
      })

      if (response.ok) {
        setSequence(prev => [...prev, newSeq])
        setNewReceived('')
        setNewResponse('')
      } else {
        console.error('Failed to save sequences')
      }
    } catch (error) {
      console.error('Error saving sequences:', error)
    }
  }

  const handleRemoveSequence = async (id: number) => {
    const newSequences = sequence.filter(seq => seq.id !== id)
    
    try {
      // Send updated sequences to backend
      const response = await fetch('http://localhost:5001/api/spi/sequences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSequences),
      })

      if (response.ok) {
        setSequence(newSequences)
      } else {
        console.error('Failed to save sequences')
      }
    } catch (error) {
      console.error('Error saving sequences:', error)
    }
  }

  const toggleRunning = async () => {
    try {
      if (!isRunning) {
        // Driver'ı yükle
        const response = await fetch('http://localhost:5001/api/spi/load-driver', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            device_name: config.device_path.replace('/dev/', ''),
            sequences: sequence.map(seq => ({
              received: seq.received,
              response: seq.response
            }))
          }),
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
          setIsRunning(true);
        } else {
          alert('Failed to load driver: ' + data.message);
        }
      } else {
        // Driver'ı kaldır
        const response = await fetch('http://localhost:5001/api/spi/unload-driver', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
          setIsRunning(false);
        } else {
          alert('Failed to unload driver: ' + data.message);
        }
      }
    } catch (error) {
      console.error('Error toggling driver:', error);
      alert('Error toggling driver. Please make sure the backend is running.');
    }
  };

  const handleExportSequences = () => {
    const dataStr = JSON.stringify(sequence, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `spi_sequences_${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const handleImportSequences = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const importedSequences = JSON.parse(e.target?.result as string)
        if (Array.isArray(importedSequences)) {
          setSequence(importedSequences)
        }
      } catch (error) {
        console.error('Error importing sequences:', error)
        alert('Invalid sequence file format')
      }
    }
    reader.readAsText(file)
  }

  // Log'ları kontrol et
  const checkLogs = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/spi/logs');
      const data = await response.json();
      
      if (data.status === 'success') {
        const newLogs = data.logs.map((log: string, index: number) => ({
          id: Date.now() + index,
          message: log,
          timestamp: new Date().toLocaleTimeString()
        }));
        
        setLogList(prev => {
          const existingIds = new Set(prev.map(log => log.message));
          const uniqueNewLogs = newLogs.filter((log: Log) => !existingIds.has(log.message));
          return [...prev, ...uniqueNewLogs];
        });
      }
    } catch (error) {
      console.error('Error checking logs:', error);
    }
  };

  // Periyodik olarak log'ları kontrol et
  useEffect(() => {
    const interval = setInterval(checkLogs, 1000);
    return () => clearInterval(interval);
  }, []);

  // Terminal'i en son satıra scroll et
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logList, commandList]); // logList veya commandList değiştiğinde scroll et

  // Check system status
  const checkSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/system/status');
      const data = await response.json();
      
      if (data.status === 'success') {
        setSystemStatus(data.data);
      }
    } catch (error) {
      console.error('Error checking system status:', error);
    }
  };

  // Periodically check system status
  useEffect(() => {
    const interval = setInterval(checkSystemStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Status Panel */}
      <div className="bg-card border-b border-border p-2">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-end gap-4">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-2">
                    <Server className={`h-4 w-4 ${systemStatus.backend.status ? 'text-green-500' : 'text-red-500'}`} />
                    <span className="text-xs text-muted-foreground">
                      Backend ({systemStatus.backend.port})
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Backend Server {systemStatus.backend.status ? 'is running' : 'is not running'}</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-2">
                    <Monitor className={`h-4 w-4 ${systemStatus.frontend.status ? 'text-green-500' : 'text-red-500'}`} />
                    <span className="text-xs text-muted-foreground">
                      Frontend ({systemStatus.frontend.port})
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Frontend Server {systemStatus.frontend.status ? 'is running' : 'is not running'}</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-2">
                    <Cpu className={`h-4 w-4 ${systemStatus.driver.status ? 'text-green-500' : 'text-red-500'}`} />
                    <span className="text-xs text-muted-foreground">
                      Driver ({systemStatus.driver.device})
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>SPI Driver {systemStatus.driver.status ? 'is loaded' : 'is not loaded'}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>

      {/* Configuration Header */}
      <div className="bg-card border-b border-border p-4">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4 flex-1">
              <div className="flex-1">
                <label className="block text-xs font-medium mb-1 text-foreground">Device Path</label>
                <input
                  type="text"
                  value={config.device_path}
                  onChange={handleConfigChange('device_path')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-foreground">Bus</label>
                <input
                  type="number"
                  value={config.bus_num}
                  onChange={handleConfigChange('bus_num')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-foreground">CS</label>
                <input
                  type="number"
                  value={config.cs_num}
                  onChange={handleConfigChange('cs_num')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-32">
                <label className="block text-xs font-medium mb-1 text-foreground">Speed (Hz)</label>
                <input
                  type="number"
                  value={config.speed}
                  onChange={handleConfigChange('speed')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-foreground">Mode</label>
                <input
                  type="number"
                  value={config.mode}
                  onChange={handleConfigChange('mode')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
              
              <div className="w-24">
                <label className="block text-xs font-medium mb-1 text-foreground">Bits</label>
                <input
                  type="number"
                  value={config.bits_per_word}
                  onChange={handleConfigChange('bits_per_word')}
                  className="w-full px-2 py-1 text-sm border rounded-md bg-background text-foreground"
                />
              </div>
            </div>

            <div className="flex items-end gap-2">
              <Button 
                onClick={handleSaveConfig}
                variant="outline"
                size="default"
                className="text-foreground hover:text-foreground h-9"
              >
                Save Config
              </Button>
              <Button 
                onClick={toggleRunning}
                variant={isRunning ? "destructive" : "default"}
                size="default"
                className="h-9"
              >
                {isRunning ? 'Stop' : 'Start'}
              </Button>
              {deviceExists && (
                <span className="text-xs text-green-500 ml-2">
                  Device Ready
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto max-w-6xl p-8 flex-grow">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sequence Management */}
          <div className="bg-card rounded-lg shadow-lg p-6 border border-border">
            <h2 className="text-2xl font-semibold mb-4 text-foreground">Sequence Management</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Received Data (Hex)</label>
                  <input
                    type="text"
                    value={newReceived}
                    onChange={(e) => setNewReceived(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background text-foreground font-mono"
                    placeholder="Enter received hex..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Response (Hex)</label>
                  <input
                    type="text"
                    value={newResponse}
                    onChange={(e) => setNewResponse(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background text-foreground font-mono"
                    placeholder="Enter response hex..."
                  />
                </div>
              </div>
              <Button onClick={handleAddSequence} className="w-full">
                Add Sequence
              </Button>

              {/* Sequence List */}
              <div className="mt-4">
                {/* Table Header */}
                <div className="grid grid-cols-[60px_1fr_1fr_60px] gap-2 mb-2 px-2">
                  <div className="text-xs font-medium text-muted-foreground">ID</div>
                  <div className="text-xs font-medium text-muted-foreground">Received Data</div>
                  <div className="text-xs font-medium text-muted-foreground">Response</div>
                  <div className="text-xs font-medium text-muted-foreground text-right">Action</div>
                </div>
                
                {/* Sequence Items */}
                <div className="space-y-2">
                  {sequence.map((seq, index) => (
                    <div key={seq.id} className="grid grid-cols-[60px_1fr_1fr_60px] gap-2 items-center p-2 bg-background/50 rounded-md">
                      <div className="text-sm text-muted-foreground">#{index + 1}</div>
                      <div className="font-mono text-sm text-green-400">{seq.received}</div>
                      <div className="font-mono text-sm text-blue-400">{seq.response}</div>
                      <div className="flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveSequence(seq.id)}
                          className="text-destructive hover:text-destructive/90"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Command Interface */}
          <div className="bg-card rounded-lg shadow-lg p-6 border border-border">
            <h2 className="text-2xl font-semibold mb-4 text-foreground">Command Interface</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1 text-foreground">Command (Hex)</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-md bg-background text-foreground font-mono"
                    placeholder="Enter hex command..."
                  />
                  <Button onClick={handleSendCommand}>
                    Send
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Terminal (Command History) */}
        <div className="mt-6">
          <div className="bg-card rounded-lg shadow-lg p-6 border border-border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold text-foreground">Terminal</h2>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setLogList([])}
                  className="text-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              </div>
            </div>
            <div 
              ref={terminalRef}
              className="bg-black/50 rounded-md p-4 font-mono text-sm h-[300px] overflow-y-auto"
            >
              {logList.map((log) => (
                <div key={log.id} className="mb-0.5">
                  <div className="text-yellow-400">{log.message}</div>
                </div>
              ))}
              {commandList.map((cmd) => (
                <div key={cmd.id} className="mb-0.5">
                  <div className="text-gray-400 text-xs">{cmd.timestamp}</div>
                  <div className="text-green-400">&gt; {cmd.command}</div>
                  <div className="text-blue-400">&lt; {cmd.response}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-card border-t border-border py-4">
        <div className="container mx-auto max-w-6xl px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="h-5 w-5 text-primary" />
              <span className="text-sm text-muted-foreground">
                Linux SPI Simulator v0.1.0 (Beta)
              </span>
            </div>
            
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/yourusername/spi-simulator"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="h-5 w-5" />
              </a>
              <span className="text-sm text-muted-foreground">
                © 2024 Linux SPI Simulator | developed by Hakan Kaya
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App 